import asyncio

from ..models.task import LogLevel, TaskLogDto
from ..repositories.task_log_repository import TaskLogRepository


class TaskLogService:
    def __init__(self, repository: TaskLogRepository):
        self.repository = repository
        self.queues: dict[str, set[asyncio.Queue[TaskLogDto]]] = {}

    def append(self, task_id: str, level: LogLevel, message: str) -> TaskLogDto:
        row = self.repository.append(task_id, level, message)
        for queue in self.queues.get(task_id, set()):
            queue.put_nowait(row)
        return row

    def list_by_task(self, task_id: str) -> list[TaskLogDto]:
        return self.repository.list_by_task(task_id)

    def subscribe(self, task_id: str) -> asyncio.Queue[TaskLogDto]:
        queue: asyncio.Queue[TaskLogDto] = asyncio.Queue()
        self.queues.setdefault(task_id, set()).add(queue)
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue[TaskLogDto]) -> None:
        self.queues.get(task_id, set()).discard(queue)
