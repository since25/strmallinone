import asyncio

from ..models.resource import ResourceDto
from ..repositories.task_repository import TaskRepository
from .task_log_service import TaskLogService


class WorkflowService:
    def __init__(self, tasks: TaskRepository, logs: TaskLogService, transfer_adapter, strm_service, strm_delay_seconds: int):
        self.tasks = tasks
        self.logs = logs
        self.transfer_adapter = transfer_adapter
        self.strm_service = strm_service
        self.strm_delay_seconds = strm_delay_seconds

    async def run(self, task_id: str, resource: ResourceDto) -> None:
        self.tasks.update_statuses(task_id, "running", "pending", "pending")
        self.logs.append(task_id, "info", "任务开始")
        self.logs.append(task_id, "info", "开始调用 p115 进行 115 转存")
        try:
            transfer = await asyncio.to_thread(self.transfer_adapter.transfer, resource)
            if not transfer.success or not transfer.data:
                self.tasks.update_statuses(task_id, "failed", "failed", "pending", transfer.message)
                self.logs.append(task_id, "error", transfer.message)
                return
            self.tasks.update_statuses(task_id, "running", "success", "pending")
            self.logs.append(task_id, "success", f"115 转存成功: {transfer.data.savePath}")
            self.logs.append(task_id, "info", f"等待 AList 刷新: {self.strm_delay_seconds} 秒")
            await asyncio.sleep(self.strm_delay_seconds)
            self.logs.append(task_id, "info", "开始生成 STRM")
            result = await asyncio.to_thread(self.strm_service.generate_for_path, transfer.data.savePath, resource.mediaType)
            if result["errors"]:
                message = result["errors"][0]
                self.tasks.update_statuses(task_id, "failed", "success", "failed", message)
                self.logs.append(task_id, "error", message)
                return
            self.tasks.update_statuses(task_id, "success", "success", "success")
            self.logs.append(
                task_id,
                "success",
                f"STRM 生成完成: 新建={len(result['created'])}, 跳过={len(result['skipped'])}",
            )
            self.logs.append(task_id, "success", "任务完成")
        except Exception as exc:
            message = str(exc)
            self.tasks.update_statuses(task_id, "failed", "failed", "failed", message)
            self.logs.append(task_id, "error", f"任务异常: {message}")
