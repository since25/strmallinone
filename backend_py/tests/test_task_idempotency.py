from pathlib import Path
import json
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend_py.app.models.resource import ResourceDto
from backend_py.app.repositories.database import Database
from backend_py.app.repositories.task_repository import TaskRepository


def make_resource() -> ResourceDto:
    return ResourceDto(
        id="legacy", title="Legacy", provider="115", mediaType="tv", rawType="video", size="-",
        shareUrl="https://115.com/s/share?password=ABCD",
        extra={"shareCode": "share", "receiveCode": "ABCD"},
    )


def test_create_or_get_reuses_active_and_success_tasks(tmp_path: Path):
    repo = TaskRepository(Database(tmp_path / "app.db"))
    first, reused = repo.create_or_get("task_1", "demo", make_resource(), "autotv")
    assert not reused
    second, reused = repo.create_or_get("task_2", "demo", make_resource(), "autotv")
    assert reused and second.id == first.id


def test_database_backfills_legacy_task_identity(tmp_path: Path):
    db_path = tmp_path / "legacy.db"
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.executescript("""CREATE TABLE transfer_tasks (id TEXT PRIMARY KEY, keyword TEXT NOT NULL, provider TEXT NOT NULL, resource_title TEXT NOT NULL, resource_json TEXT NOT NULL, status TEXT NOT NULL, transfer_status TEXT NOT NULL, strm_status TEXT NOT NULL, error_message TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);""")
    resource = make_resource()
    conn.execute("INSERT INTO transfer_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ("legacy_1", "demo", "115", resource.title, json.dumps(resource.model_dump()), "success", "success", "success", None, "now", "now"))
    conn.commit(); conn.close()
    db = Database(db_path)
    row = db.connect().execute("SELECT resource_key, target_folder FROM transfer_tasks WHERE id = 'legacy_1'").fetchone()
    assert row["resource_key"] == "115:share:ABCD"
    assert row["target_folder"] == "autotv"
