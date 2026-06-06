from datetime import UTC, datetime

from ..models.resource import ResourceDto
from ..models.task import StepStatus, TaskDto, TaskStatus
from .database import Database


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def row_to_task(row) -> TaskDto:
    return TaskDto(
        id=row["id"],
        keyword=row["keyword"],
        provider=row["provider"],
        resourceTitle=row["resource_title"],
        resource=ResourceDto.model_validate_json(row["resource_json"]),
        status=row["status"],
        transferStatus=row["transfer_status"],
        strmStatus=row["strm_status"],
        errorMessage=row["error_message"],
        createdAt=row["created_at"],
        updatedAt=row["updated_at"],
    )


class TaskRepository:
    def __init__(self, db: Database):
        self.db = db

    def create(self, task_id: str, keyword: str, resource: ResourceDto) -> None:
        ts = now_iso()
        self.db.execute(
            """
            INSERT INTO transfer_tasks (
              id, keyword, provider, resource_title, resource_json, status,
              transfer_status, strm_status, error_message, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                keyword,
                resource.provider,
                resource.title,
                resource.model_dump_json(),
                "pending",
                "pending",
                "pending",
                None,
                ts,
                ts,
            ),
        )

    def find_by_id(self, task_id: str) -> TaskDto | None:
        conn = self.db.connect()
        try:
            row = conn.execute("SELECT * FROM transfer_tasks WHERE id = ?", (task_id,)).fetchone()
            return row_to_task(row) if row else None
        finally:
            conn.close()

    def update_statuses(
        self,
        task_id: str,
        status: TaskStatus,
        transfer_status: StepStatus,
        strm_status: StepStatus,
        error_message: str | None = None,
    ) -> None:
        self.db.execute(
            """
            UPDATE transfer_tasks
            SET status = ?, transfer_status = ?, strm_status = ?, error_message = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, transfer_status, strm_status, error_message, now_iso(), task_id),
        )
