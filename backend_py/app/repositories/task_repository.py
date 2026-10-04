from datetime import UTC, datetime

from ..models.resource import ResourceDto
from ..models.task import StepStatus, TaskDto, TaskStatus
from ..services.resource_identity import resource_key
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
        resourceKey=row["resource_key"] if "resource_key" in row.keys() else None,
        targetFolder=row["target_folder"] if "target_folder" in row.keys() else None,
        duplicate=bool(row["duplicate"]) if "duplicate" in row.keys() else False,
        retryCount=int(row["retry_count"] or 0) if "retry_count" in row.keys() else 0,
        createdAt=row["created_at"],
        updatedAt=row["updated_at"],
    )


class TaskRepository:
    def __init__(self, db: Database):
        self.db = db

    def create(
        self,
        task_id: str,
        keyword: str,
        resource: ResourceDto,
        resource_key_value: str | None = None,
        target_folder: str | None = None,
    ) -> None:
        ts = now_iso()
        self.db.execute(
            """
            INSERT INTO transfer_tasks (
              id, keyword, provider, resource_title, resource_json, status,
              transfer_status, strm_status, error_message, created_at, updated_at,
              resource_key, target_folder
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                resource_key_value or resource_key(resource),
                target_folder,
            ),
        )

    def find_active_by_resource_key(self, resource_key: str, target_folder: str) -> TaskDto | None:
        conn = self.db.connect()
        try:
            row = conn.execute(
                "SELECT * FROM transfer_tasks WHERE resource_key = ? AND target_folder = ? "
                "AND status IN ('pending', 'running', 'success') ORDER BY created_at DESC LIMIT 1",
                (resource_key, target_folder),
            ).fetchone()
            return row_to_task(row) if row else None
        finally:
            conn.close()

    def create_or_get(
        self,
        task_id: str,
        keyword: str,
        resource: ResourceDto,
        target_folder: str,
        resource_key_value: str | None = None,
    ) -> tuple[TaskDto, bool]:
        key = resource_key_value or resource_key(resource)
        conn = self.db.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM transfer_tasks WHERE resource_key = ? AND target_folder = ? "
                "AND status IN ('pending', 'running', 'success') ORDER BY created_at DESC LIMIT 1",
                (key, target_folder),
            ).fetchone()
            if row:
                conn.commit()
                return row_to_task(row), True
            ts = now_iso()
            conn.execute(
                """INSERT INTO transfer_tasks (
                  id, keyword, provider, resource_title, resource_json, status,
                  transfer_status, strm_status, error_message, created_at, updated_at,
                  resource_key, target_folder, duplicate, retry_count
                ) VALUES (?, ?, ?, ?, ?, 'pending', 'pending', 'pending', NULL, ?, ?, ?, ?, 0, 0)""",
                (task_id, keyword, resource.provider, resource.title, resource.model_dump_json(), ts, ts, key, target_folder),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        task = self.find_by_id(task_id)
        if task is None:
            raise RuntimeError(f"failed to create task {task_id}")
        return task, False

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
        duplicate: bool | None = None,
    ) -> None:
        duplicate_sql = "" if duplicate is None else ", duplicate = ?"
        params: list[object] = [status, transfer_status, strm_status, error_message]
        if duplicate is not None:
            params.append(int(duplicate))
        params.extend([now_iso(), task_id])
        self.db.execute(
            f"""
            UPDATE transfer_tasks
            SET status = ?, transfer_status = ?, strm_status = ?, error_message = ?{duplicate_sql}, updated_at = ?
            WHERE id = ?
            """,
            params,
        )

    def increment_retry(self, task_id: str) -> None:
        self.db.execute(
            "UPDATE transfer_tasks SET retry_count = retry_count + 1, status = 'pending', "
            "transfer_status = 'pending', strm_status = 'pending', error_message = NULL, updated_at = ? WHERE id = ?",
            (now_iso(), task_id),
        )

    def delete_pending(self, task_id: str) -> None:
        """Compensate a failed batch insert without touching reused tasks."""
        self.db.execute(
            "DELETE FROM transfer_tasks WHERE id = ? AND status = 'pending' AND retry_count = 0",
            (task_id,),
        )

    def mark_failed(self, task_id: str, message: str) -> None:
        self.db.execute(
            "UPDATE transfer_tasks SET status = 'failed', transfer_status = 'failed', "
            "error_message = ?, updated_at = ? WHERE id = ? AND status IN ('pending', 'running')",
            (message, now_iso(), task_id),
        )
