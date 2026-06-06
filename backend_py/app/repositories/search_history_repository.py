from datetime import UTC, datetime

from .database import Database


class SearchHistoryRepository:
    def __init__(self, db: Database):
        self.db = db

    def create(self, keyword: str, driver: str, result_count: int) -> None:
        self.db.execute(
            "INSERT INTO search_history (keyword, driver, result_count, created_at) VALUES (?, ?, ?, ?)",
            (keyword, driver, result_count, datetime.now(UTC).isoformat()),
        )
