from datetime import UTC, datetime

from ..models.task import LogLevel, TaskLogDto
from .database import Database


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class TaskLogRepository:
    def __init__(self, db: Database):
        self.db = db

    def append(self, task_id: str, level: LogLevel, message: str) -> TaskLogDto:
        created_at = now_iso()
        conn = self.db.connect()
        try:
            cur = conn.execute(
                "INSERT INTO task_logs (task_id, level, message, created_at) VALUES (?, ?, ?, ?)",
                (task_id, level, message, created_at),
            )
            conn.commit()
            log_id = int(cur.lastrowid)
            return TaskLogDto(id=log_id, taskId=task_id, level=level, message=message, createdAt=created_at)
        finally:
            conn.close()

    def list_by_task(self, task_id: str) -> list[TaskLogDto]:
        conn = self.db.connect()
        try:
            rows = conn.execute(
                "SELECT * FROM task_logs WHERE task_id = ? ORDER BY id ASC",
                (task_id,),
            ).fetchall()
            return [
                TaskLogDto(
                    id=row["id"],
                    taskId=row["task_id"],
                    level=row["level"],
                    message=row["message"],
                    createdAt=row["created_at"],
                )
                for row in rows
            ]
        finally:
            conn.close()
