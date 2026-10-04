from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend_py.app.models.batch import CreateBatchRequest
from backend_py.app.models.resource import ResourceDto
from backend_py.app.repositories.batch_repository import BatchRepository
from backend_py.app.repositories.database import Database
from backend_py.app.repositories.task_repository import TaskRepository
from backend_py.app.services.batch_service import BatchService
from backend_py.app.services.batch_service import is_transient_error


def test_concurrency_is_clamped_to_supported_range():
    item = ResourceDto(id="x", title="x", provider="115", mediaType="movie", rawType="video", size="-", shareUrl="https://115.com/s/x?password=ABCD", extra={"shareCode": "x", "receiveCode": "ABCD"})
    payload = CreateBatchRequest(items=[item], concurrency=99)
    assert payload.concurrency == 4
    payload = CreateBatchRequest(items=[item], concurrency=0)
    assert payload.concurrency == 1


@pytest.mark.parametrize("message", ["timeout", "connection reset", "HTTP 503 temporarily unavailable", "HTTP 500 server error"])
def test_transient_errors_are_retryable(message: str):
    assert is_transient_error(message)


@pytest.mark.parametrize("message", ["资源缺少 115 shareCode", "权限不足", "提取码错误"])
def test_permanent_errors_are_not_retryable(message: str):
    assert not is_transient_error(message)


@pytest.mark.asyncio
async def test_batch_retries_transient_task_failures(tmp_path: Path):
    db = Database(tmp_path / "batch.db")
    tasks = TaskRepository(db)
    batches = BatchRepository(db)
    calls = {"count": 0}

    class FakeWorkflow:
        async def run(self, task_id: str, resource: ResourceDto) -> None:
            calls["count"] += 1
            if calls["count"] < 3:
                tasks.update_statuses(task_id, "failed", "failed", "pending", "timeout from upstream")
            else:
                tasks.update_statuses(task_id, "success", "success", "success")

    resource = ResourceDto(id="x", title="x", provider="115", mediaType="movie", rawType="video", size="-", shareUrl="https://115.com/s/x?password=ABCD", extra={"shareCode": "x", "receiveCode": "ABCD"})
    service = BatchService(batches, tasks, FakeWorkflow(), "automv", "autotv")
    batch = service.create_batch("x", [resource])
    await service.run(batch.id)
    items = batches.list_items(batch.id)
    assert calls["count"] == 3
    assert items[0].status == "success"
    assert tasks.find_by_id(items[0].taskId).retryCount == 2


@pytest.mark.asyncio
async def test_reused_pending_task_times_out_instead_of_hanging(tmp_path: Path):
    db = Database(tmp_path / "batch-timeout.db")
    tasks = TaskRepository(db)
    batches = BatchRepository(db)
    resource = ResourceDto(id="x", title="x", provider="115", mediaType="movie", rawType="video", size="-", shareUrl="https://115.com/s/x?password=ABCD", extra={"shareCode": "x", "receiveCode": "ABCD"})
    service = BatchService(batches, tasks, object(), "automv", "autotv", reused_wait_timeout_seconds=0.01)
    service.create_batch("first", [resource])
    second = service.create_batch("second", [resource])
    await service.run(second.id)
    item = batches.list_items(second.id)[0]
    assert item.status == "failed"
    assert item.errorMessage == "复用任务等待超时，请重新提交"
    stale = tasks.find_by_id(item.taskId)
    assert stale.status == "failed"
    replacement, reused = tasks.create_or_get("replacement", "third", resource, "automv")
    assert replacement.id != stale.id
    assert not reused


def test_batch_compensation_deletes_only_new_pending_tasks(tmp_path: Path):
    db = Database(tmp_path / "batch-compensation.db")
    tasks = TaskRepository(db)
    batches = BatchRepository(db)
    first = ResourceDto(id="first", title="first", provider="115", mediaType="movie", rawType="video", size="-", shareUrl="https://115.com/s/first?password=ABCD", extra={"shareCode": "first", "receiveCode": "ABCD"})
    second = ResourceDto(id="second", title="second", provider="115", mediaType="movie", rawType="video", size="-", shareUrl="https://115.com/s/second?password=EFGH", extra={"shareCode": "second", "receiveCode": "EFGH"})
    existing, _ = tasks.create_or_get("existing", "old", first, "automv")

    class FailingBatchRepository(BatchRepository):
        def __init__(self, database):
            super().__init__(database)
            self.calls = 0

        def add_item(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 2:
                raise RuntimeError("item insert failed")
            return super().add_item(*args, **kwargs)

    failing = FailingBatchRepository(db)
    service = BatchService(failing, tasks, object(), "automv", "autotv")
    with pytest.raises(RuntimeError, match="item insert failed"):
        service.create_batch("demo", [first, second])
    assert tasks.find_by_id(existing.id) is not None
    assert tasks.find_active_by_resource_key("115:second:EFGH", "automv") is None
    assert db.connect().execute("SELECT COUNT(*) FROM transfer_batches").fetchone()[0] == 0
