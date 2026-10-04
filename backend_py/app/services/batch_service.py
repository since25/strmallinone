import asyncio
import re
import time
from uuid import uuid4

from ..models.batch import BatchDto, BatchItemDto
from ..models.resource import ResourceDto
from ..repositories.batch_repository import BatchRepository
from ..repositories.task_repository import TaskRepository
from .resource_identity import dedupe_resources, resource_key, target_folder


def is_transient_error(message: str | None) -> bool:
    value = (message or "").lower()
    markers = ("timeout", "timed out", "connection", "temporar", "503", "502", "504", "429", "busy", "network")
    permanent = ("缺少", "无效", "invalid", "permission", "权限", "密码", "提取码", "分享链接为空", "未找到目标目录")
    return (any(marker in value for marker in markers) or bool(re.search(r"\b5\d{2}\b", value))) and not any(marker in value for marker in permanent)


class BatchService:
    max_retries = 2

    def __init__(self, batches: BatchRepository, tasks: TaskRepository, workflow_service, movie_folder: str, tv_folder: str, reused_wait_timeout_seconds: float = 30.0):
        self.batches = batches
        self.tasks = tasks
        self.workflow_service = workflow_service
        self.movie_folder = movie_folder
        self.tv_folder = tv_folder
        self.reused_wait_timeout_seconds = reused_wait_timeout_seconds

    def create_batch(self, keyword: str, resources: list[ResourceDto], concurrency: int = 2) -> BatchDto:
        concurrency = max(1, min(4, int(concurrency)))
        unique_resources = dedupe_resources(resources)
        batch_id = f"batch_{uuid4().hex[:10]}"
        created_task_ids: list[str] = []
        self.batches.create(batch_id, keyword, concurrency, len(unique_resources))
        try:
            for resource in unique_resources:
                key = resource_key(resource)
                folder = target_folder(resource, self.movie_folder, self.tv_folder)
                task, reused = self.tasks.create_or_get(f"task_{uuid4().hex[:10]}", keyword, resource, folder, key)
                if not reused:
                    created_task_ids.append(task.id)
                item_status = "skipped" if reused and task.status == "success" else "pending"
                self.batches.add_item(
                    f"item_{uuid4().hex[:10]}", batch_id, task.id, key, resource,
                    status=item_status, duplicate=bool(task.duplicate), reused=reused,
                )
            return self.batches.refresh_counts(batch_id) or self.batches.find_by_id(batch_id)  # type: ignore[return-value]
        except Exception:
            self.batches.delete_batch(batch_id)
            for task_id in created_task_ids:
                self.tasks.delete_pending(task_id)
            raise

    async def _wait_for_reused_task(self, item: BatchItemDto) -> object:
        started = time.monotonic()
        while True:
            task = self.tasks.find_by_id(item.taskId or "")
            if task is None or task.status not in {"pending", "running"}:
                return task
            if time.monotonic() - started >= self.reused_wait_timeout_seconds:
                message = "复用任务等待超时，请重新提交"
                if task is not None:
                    self.tasks.mark_failed(task.id, message)
                raise RuntimeError(message)
            await asyncio.sleep(0.05)

    async def _run_item(self, item: BatchItemDto) -> object:
        if not item.taskId:
            raise RuntimeError("批次项缺少任务 ID")
        if item.reused:
            return await self._wait_for_reused_task(item)
        await self.workflow_service.run(item.taskId, item.resource)
        return self.tasks.find_by_id(item.taskId)

    async def _execute_with_retry(self, item: BatchItemDto) -> tuple[str, str | None, bool]:
        for _attempt in range(self.max_retries + 1):
            try:
                task = await self._run_item(item)
            except Exception as exc:
                message = str(exc)
                task = self.tasks.find_by_id(item.taskId or "")
                retry_count = task.retryCount if task is not None else _attempt
                if not item.reused and is_transient_error(message) and retry_count < self.max_retries:
                    if task is not None:
                        self.tasks.increment_retry(task.id)
                    self.batches.increment_retry(item.id)
                    continue
                return "failed", message or "任务异常", False
            if task is None:
                return "failed", "任务不存在", False
            if task.status == "success":
                return ("skipped" if item.reused or task.duplicate else "success"), None, bool(task.duplicate)
            if item.reused:
                return "failed", task.errorMessage or "复用任务失败", False
            if not is_transient_error(task.errorMessage) or task.retryCount >= self.max_retries:
                return "failed", task.errorMessage or "任务失败", False
            self.tasks.increment_retry(task.id)
            self.batches.increment_retry(item.id)
        return "failed", "瞬时错误重试次数已耗尽", False

    async def run(self, batch_id: str) -> None:
        batch = self.batches.find_by_id(batch_id)
        if batch is None:
            return
        items = [item for item in self.batches.list_items(batch_id) if item.status == "pending"]
        if not items:
            self.batches.refresh_counts(batch_id)
            return
        queue: asyncio.Queue[BatchItemDto] = asyncio.Queue()
        for item in items:
            queue.put_nowait(item)
        self.batches.refresh_counts(batch_id, status="running")

        async def worker() -> None:
            while True:
                try:
                    item = queue.get_nowait()
                except asyncio.QueueEmpty:
                    return
                self.batches.update_item(item.id, "running")
                self.batches.refresh_counts(batch_id)
                try:
                    status, error, duplicate = await self._execute_with_retry(item)
                    self.batches.update_item(item.id, status, duplicate=duplicate, error_message=error)
                except Exception as exc:
                    self.batches.update_item(item.id, "failed", error_message=str(exc))
                finally:
                    self.batches.refresh_counts(batch_id)
                    queue.task_done()

        await asyncio.gather(*(worker() for _ in range(min(batch.concurrency, len(items)))))
        self.batches.refresh_counts(batch_id)
