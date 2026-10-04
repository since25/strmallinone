import json
from datetime import UTC, datetime

from ..models.batch import BatchDto, BatchItemDto
from ..models.resource import ResourceDto
from .database import Database


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def row_to_batch(row) -> BatchDto:
    return BatchDto(
        id=row["id"], keyword=row["keyword"], status=row["status"], concurrency=row["concurrency"],
        totalCount=row["total_count"], pendingCount=row["pending_count"], runningCount=row["running_count"],
        successCount=row["success_count"], skippedCount=row["skipped_count"], failedCount=row["failed_count"],
        errorMessage=row["error_message"], createdAt=row["created_at"], updatedAt=row["updated_at"],
    )


def row_to_item(row) -> BatchItemDto:
    return BatchItemDto(
        id=row["id"], batchId=row["batch_id"], taskId=row["task_id"], resourceKey=row["resource_key"],
        resource=ResourceDto.model_validate_json(row["resource_json"]), status=row["status"],
        duplicate=bool(row["duplicate"]), reused=bool(row["reused"]), errorMessage=row["error_message"], retryCount=row["retry_count"],
        createdAt=row["created_at"], updatedAt=row["updated_at"],
    )


class BatchRepository:
    def __init__(self, db: Database):
        self.db = db

    def create(self, batch_id: str, keyword: str, concurrency: int, total_count: int) -> BatchDto:
        ts = now_iso()
        self.db.execute(
            """INSERT INTO transfer_batches
            (id, keyword, status, concurrency, total_count, pending_count, running_count,
             success_count, skipped_count, failed_count, error_message, created_at, updated_at)
            VALUES (?, ?, 'pending', ?, ?, ?, 0, 0, 0, 0, NULL, ?, ?)""",
            (batch_id, keyword, concurrency, total_count, total_count, ts, ts),
        )
        batch = self.find_by_id(batch_id)
        if not batch:
            raise RuntimeError(f"failed to create batch {batch_id}")
        return batch

    def add_item(self, item_id: str, batch_id: str, task_id: str | None, key: str, resource: ResourceDto, status: str = "pending", duplicate: bool = False, error_message: str | None = None, reused: bool = False) -> None:
        ts = now_iso()
        self.db.execute(
            """INSERT INTO transfer_items
            (id, batch_id, task_id, resource_key, resource_json, status, duplicate, reused, error_message, retry_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
            (item_id, batch_id, task_id, key, resource.model_dump_json(), status, int(duplicate), int(reused), error_message, ts, ts),
        )

    def find_by_id(self, batch_id: str) -> BatchDto | None:
        conn = self.db.connect()
        try:
            row = conn.execute("SELECT * FROM transfer_batches WHERE id = ?", (batch_id,)).fetchone()
            return row_to_batch(row) if row else None
        finally:
            conn.close()

    def list_items(self, batch_id: str) -> list[BatchItemDto]:
        conn = self.db.connect()
        try:
            rows = conn.execute("SELECT * FROM transfer_items WHERE batch_id = ? ORDER BY created_at, id", (batch_id,)).fetchall()
            return [row_to_item(row) for row in rows]
        finally:
            conn.close()

    def update_item(self, item_id: str, status: str, task_id: str | None = None, duplicate: bool | None = None, error_message: str | None = None) -> None:
        sets = ["status = ?", "updated_at = ?"]
        params: list[object] = [status, now_iso()]
        if task_id is not None:
            sets.append("task_id = ?"); params.append(task_id)
        if duplicate is not None:
            sets.append("duplicate = ?"); params.append(int(duplicate))
        if error_message is not None:
            sets.append("error_message = ?"); params.append(error_message)
        params.append(item_id)
        self.db.execute(f"UPDATE transfer_items SET {', '.join(sets)} WHERE id = ?", params)

    def increment_retry(self, item_id: str) -> None:
        self.db.execute("UPDATE transfer_items SET retry_count = retry_count + 1, updated_at = ? WHERE id = ?", (now_iso(), item_id))

    def delete_batch(self, batch_id: str) -> None:
        conn = self.db.connect()
        try:
            conn.execute("DELETE FROM transfer_items WHERE batch_id = ?", (batch_id,))
            conn.execute("DELETE FROM transfer_batches WHERE id = ?", (batch_id,))
            conn.commit()
        finally:
            conn.close()

    def refresh_counts(self, batch_id: str, status: str | None = None, error_message: str | None = None) -> BatchDto | None:
        conn = self.db.connect()
        try:
            if status is not None:
                sets = ["status = ?", "updated_at = ?"]
                params: list[object] = [status, now_iso()]
                if error_message is not None:
                    sets.append("error_message = ?"); params.append(error_message)
                params.append(batch_id)
                conn.execute(f"UPDATE transfer_batches SET {', '.join(sets)} WHERE id = ?", params)
            counts = {row["status"]: row["count"] for row in conn.execute("SELECT status, COUNT(*) count FROM transfer_items WHERE batch_id = ? GROUP BY status", (batch_id,)).fetchall()}
            total = sum(counts.values())
            pending, running = counts.get("pending", 0), counts.get("running", 0)
            success, skipped, failed = counts.get("success", 0), counts.get("skipped", 0), counts.get("failed", 0)
            current = conn.execute("SELECT status FROM transfer_batches WHERE id = ?", (batch_id,)).fetchone()
            current_status = current["status"] if current else "pending"
            if total and pending == 0 and running == 0:
                current_status = "success" if failed == 0 else ("failed" if success + skipped == 0 else "partial")
            elif running or pending:
                current_status = "running"
            conn.execute("""UPDATE transfer_batches SET status = ?, total_count = ?, pending_count = ?, running_count = ?, success_count = ?, skipped_count = ?, failed_count = ?, updated_at = ? WHERE id = ?""", (current_status, total, pending, running, success, skipped, failed, now_iso(), batch_id))
            conn.commit()
            row = conn.execute("SELECT * FROM transfer_batches WHERE id = ?", (batch_id,)).fetchone()
            return row_to_batch(row) if row else None
        finally:
            conn.close()
