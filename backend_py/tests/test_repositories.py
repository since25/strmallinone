from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend_py.app.models.resource import ResourceDto
from backend_py.app.repositories.database import Database
from backend_py.app.repositories.search_history_repository import SearchHistoryRepository
from backend_py.app.repositories.task_log_repository import TaskLogRepository
from backend_py.app.repositories.task_repository import TaskRepository


def test_task_repository_round_trip(tmp_path: Path):
    db = Database(tmp_path / "app.db")
    tasks = TaskRepository(db)
    resource = ResourceDto(
        id="pansou_sabc_ABCD",
        title="Example Movie",
        provider="115",
        mediaType="movie",
        rawType="video",
        size="-",
        shareUrl="https://115cdn.com/s/sabc?password=ABCD",
        extra={"source": "pansou", "shareCode": "sabc", "receiveCode": "ABCD"},
    )

    tasks.create("task_1", "example", resource)
    task = tasks.find_by_id("task_1")

    assert task is not None
    assert task.id == "task_1"
    assert task.status == "pending"
    assert task.transferStatus == "pending"
    assert task.strmStatus == "pending"
    assert task.resourceTitle == "Example Movie"
    assert task.resource.extra["shareCode"] == "sabc"


def test_log_repository_orders_logs(tmp_path: Path):
    db = Database(tmp_path / "app.db")
    logs = TaskLogRepository(db)

    logs.append("task_1", "info", "first")
    logs.append("task_1", "success", "second")

    rows = logs.list_by_task("task_1")
    assert [row.message for row in rows] == ["first", "second"]
    assert rows[0].level == "info"
    assert rows[1].level == "success"


def test_search_history_repository_writes_count(tmp_path: Path):
    db = Database(tmp_path / "app.db")
    history = SearchHistoryRepository(db)

    history.create(keyword="movie", driver="115", result_count=3)

    conn = db.connect()
    try:
        rows = conn.execute("SELECT keyword, driver, result_count FROM search_history").fetchall()
        assert [tuple(row) for row in rows] == [("movie", "115", 3)]
    finally:
        conn.close()
