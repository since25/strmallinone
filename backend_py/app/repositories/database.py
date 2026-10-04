import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path


class Database:
    def __init__(self, path: Path, default_movie_folder: str = "automv", default_tv_folder: str = "autotv"):
        self.path = path
        self.default_movie_folder = default_movie_folder
        self.default_tv_folder = default_tv_folder
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def execute(self, sql: str, params: Iterable[object] = ()) -> None:
        conn = self.connect()
        try:
            conn.execute(sql, tuple(params))
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        conn = self.connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS transfer_tasks (
                  id TEXT PRIMARY KEY,
                  keyword TEXT NOT NULL,
                  provider TEXT NOT NULL,
                  resource_title TEXT NOT NULL,
                  resource_json TEXT NOT NULL,
                  status TEXT NOT NULL,
                  transfer_status TEXT NOT NULL,
                  strm_status TEXT NOT NULL,
                  error_message TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  resource_key TEXT,
                  target_folder TEXT,
                  duplicate INTEGER NOT NULL DEFAULT 0,
                  retry_count INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS task_logs (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  task_id TEXT NOT NULL,
                  level TEXT NOT NULL,
                  message TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS search_history (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  keyword TEXT NOT NULL,
                  driver TEXT NOT NULL,
                  result_count INTEGER NOT NULL,
                  created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS transfer_batches (
                  id TEXT PRIMARY KEY,
                  keyword TEXT NOT NULL,
                  status TEXT NOT NULL,
                  concurrency INTEGER NOT NULL,
                  total_count INTEGER NOT NULL DEFAULT 0,
                  pending_count INTEGER NOT NULL DEFAULT 0,
                  running_count INTEGER NOT NULL DEFAULT 0,
                  success_count INTEGER NOT NULL DEFAULT 0,
                  skipped_count INTEGER NOT NULL DEFAULT 0,
                  failed_count INTEGER NOT NULL DEFAULT 0,
                  error_message TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS transfer_items (
                  id TEXT PRIMARY KEY,
                  batch_id TEXT NOT NULL,
                  task_id TEXT,
                  resource_key TEXT NOT NULL,
                  resource_json TEXT NOT NULL,
                  status TEXT NOT NULL,
                  duplicate INTEGER NOT NULL DEFAULT 0,
                  reused INTEGER NOT NULL DEFAULT 0,
                  error_message TEXT,
                  retry_count INTEGER NOT NULL DEFAULT 0,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  FOREIGN KEY(batch_id) REFERENCES transfer_batches(id)
                );
                """
            )
            # The application previously shipped a smaller transfer_tasks table.
            # Additive migrations keep existing installations and test fixtures
            # readable without dropping user task history.
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(transfer_tasks)")}
            for name, definition in {
                "resource_key": "TEXT",
                "target_folder": "TEXT",
                "duplicate": "INTEGER NOT NULL DEFAULT 0",
                "retry_count": "INTEGER NOT NULL DEFAULT 0",
            }.items():
                if name not in columns:
                    conn.execute(f"ALTER TABLE transfer_tasks ADD COLUMN {name} {definition}")
            item_columns = {row["name"] for row in conn.execute("PRAGMA table_info(transfer_items)")}
            if "reused" not in item_columns:
                conn.execute("ALTER TABLE transfer_items ADD COLUMN reused INTEGER NOT NULL DEFAULT 0")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transfer_tasks_resource_target "
                "ON transfer_tasks(resource_key, target_folder, status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transfer_items_batch_status "
                "ON transfer_items(batch_id, status)"
            )
            self._backfill_task_identity(conn)
            conn.commit()
        finally:
            conn.close()

    def _backfill_task_identity(self, conn: sqlite3.Connection) -> None:
        """Populate identity columns for rows written before the migration."""
        rows = conn.execute(
            "SELECT id, resource_json FROM transfer_tasks WHERE resource_key IS NULL OR target_folder IS NULL"
        ).fetchall()
        for row in rows:
            try:
                data = json.loads(row["resource_json"])
                provider = str(data.get("provider") or "115")
                resource_id = str(data.get("id") or row["id"])
                extra = data.get("extra") if isinstance(data.get("extra"), dict) else {}
                share = str(extra.get("shareCode") or "").strip()
                receive = str(extra.get("receiveCode") or "").strip()
                key = f"{provider}:{share}:{receive}" if share and receive else f"{provider}:id:{resource_id}"
                folder = self.default_tv_folder if data.get("mediaType") == "tv" else self.default_movie_folder
            except (TypeError, ValueError, json.JSONDecodeError):
                key = f"115:id:{row['id']}"
                folder = self.default_movie_folder
            conn.execute(
                "UPDATE transfer_tasks SET resource_key = COALESCE(resource_key, ?), target_folder = COALESCE(target_folder, ?) WHERE id = ?",
                (key, folder, row["id"]),
            )
