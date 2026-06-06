import sqlite3
from collections.abc import Iterable
from pathlib import Path


class Database:
    def __init__(self, path: Path):
        self.path = path
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
                  updated_at TEXT NOT NULL
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
                """
            )
            conn.commit()
        finally:
            conn.close()
