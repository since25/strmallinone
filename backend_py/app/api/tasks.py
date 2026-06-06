import asyncio
import json
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..models.resource import ResourceDto

router = APIRouter()


class CreateTaskRequest(BaseModel):
    keyword: str
    resource: ResourceDto


@router.post("/tasks/transfer", status_code=201)
async def create_transfer_task(payload: CreateTaskRequest, request: Request):
    task_id = f"task_{uuid4().hex[:10]}"
    request.app.state.task_repository.create(task_id, payload.keyword, payload.resource)
    request.app.state.task_log_service.append(task_id, "info", "任务已创建，等待执行")
    asyncio.create_task(request.app.state.workflow_service.run(task_id, payload.resource))
    return {"success": True, "data": {"taskId": task_id}}


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
