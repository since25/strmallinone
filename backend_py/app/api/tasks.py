import asyncio
import json
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..adapters.pansou import parse_115_share_text
from ..models.resource import MediaType, ResourceDto
from ..models.batch import CreateBatchRequest
from ..services.resource_identity import resource_key, target_folder

router = APIRouter()


class CreateTaskRequest(BaseModel):
    keyword: str
    resource: ResourceDto


class ManualTransferRequest(BaseModel):
    shareText: str
    mediaType: MediaType


@router.post("/tasks/transfer", status_code=201)
async def create_transfer_task(payload: CreateTaskRequest, request: Request):
    batch_service = request.app.state.batch_service
    folder = target_folder(payload.resource, batch_service.movie_folder, batch_service.tv_folder)
    task, reused = request.app.state.task_repository.create_or_get(
        f"task_{uuid4().hex[:10]}", payload.keyword, payload.resource, folder, resource_key(payload.resource)
    )
    if not reused:
        request.app.state.task_log_service.append(task.id, "info", "任务已创建，等待执行")
        asyncio.create_task(request.app.state.workflow_service.run(task.id, payload.resource))
    return {"success": True, "data": {"taskId": task.id, "reused": reused}}


@router.post("/tasks/manual-transfer", status_code=201)
async def create_manual_transfer_task(payload: ManualTransferRequest, request: Request):
    parsed = parse_115_share_text(payload.shareText)
    if not parsed:
        raise HTTPException(status_code=400, detail="未找到有效的 115 分享链接或提取码")
    share_url, share_code, receive_code = parsed
    resource = ResourceDto(
        id=f"manual_{share_code}_{receive_code}",
        title=f"手动 115 转存 {share_code}",
        provider="115",
        mediaType=payload.mediaType,
        rawType="video",
        size="-",
        shareUrl=share_url,
        extra={"source": "manual", "shareCode": share_code, "receiveCode": receive_code},
    )
    batch_service = request.app.state.batch_service
    folder = target_folder(resource, batch_service.movie_folder, batch_service.tv_folder)
    task, reused = request.app.state.task_repository.create_or_get(
        f"task_{uuid4().hex[:10]}", "手动 115 转存", resource, folder, resource_key(resource)
    )
    if not reused:
        request.app.state.task_log_service.append(task.id, "info", "手动 115 转存任务已创建，等待执行")
        asyncio.create_task(request.app.state.workflow_service.run(task.id, resource))
    return {"success": True, "data": {"taskId": task.id, "reused": reused}}


@router.post("/batches/transfer", status_code=201)
async def create_batch_transfer(payload: CreateBatchRequest, request: Request):
    batch = request.app.state.batch_service.create_batch(payload.keyword, payload.items, payload.concurrency)
    asyncio.create_task(request.app.state.batch_service.run(batch.id))
    return {"success": True, "data": batch.model_dump()}


@router.get("/batches/{batch_id}")
def get_batch(batch_id: str, request: Request):
    batch = request.app.state.batch_repository.find_by_id(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    return {"success": True, "data": batch.model_dump()}


@router.get("/batches/{batch_id}/items")
def get_batch_items(batch_id: str, request: Request):
    if request.app.state.batch_repository.find_by_id(batch_id) is None:
        raise HTTPException(status_code=404, detail="batch not found")
    items = request.app.state.batch_repository.list_items(batch_id)
    return {"success": True, "data": [item.model_dump() for item in items]}


@router.get("/tasks/{task_id}")
def get_task(task_id: str, request: Request):
    task = request.app.state.task_repository.find_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return {"success": True, "data": task.model_dump()}


@router.get("/tasks/{task_id}/logs")
def get_logs(task_id: str, request: Request):
    logs = request.app.state.task_log_service.list_by_task(task_id)
    return {"success": True, "data": [row.model_dump() for row in logs]}


@router.get("/tasks/{task_id}/logs/stream")
async def stream_logs(task_id: str, request: Request):
    service = request.app.state.task_log_service
    queue = service.subscribe(task_id)

    async def events():
        try:
            for row in service.list_by_task(task_id):
                yield f"event: log\ndata: {json.dumps(row.model_dump(), ensure_ascii=False)}\n\n"
            while True:
                row = await queue.get()
                yield f"event: log\ndata: {json.dumps(row.model_dump(), ensure_ascii=False)}\n\n"
        finally:
            service.unsubscribe(task_id, queue)

    return StreamingResponse(events(), media_type="text/event-stream")
