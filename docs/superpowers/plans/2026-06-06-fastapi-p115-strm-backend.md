# FastAPI p115 STRM Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Node/Express + CloudSaver backend with a FastAPI backend that uses PanSou search, p115 Cookie based 115 transfer, AList refresh, and built-in STRM generation while preserving the current frontend API.

**Architecture:** Build a new `backend_py/` service beside the existing backend, reach API parity, then switch Docker to FastAPI. Keep the React frontend API contract stable and keep AList in the workflow because Emby playback depends on AList `/d` 302 URLs.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, pydantic-settings, httpx, sqlite3, pytest, p115client, Docker, existing React/Vite frontend.

---

## File Structure

- Create `backend_py/requirements.txt`: Python runtime and test dependencies.
- Create `backend_py/app/main.py`: FastAPI app construction, CORS, router mounting.
- Create `backend_py/app/config.py`: typed environment configuration.
- Create `backend_py/app/models/resource.py`: provider, media type, resource DTO models.
- Create `backend_py/app/models/task.py`: task status, task row, log row, response models.
- Create `backend_py/app/models/transfer.py`: p115 transfer result models.
- Create `backend_py/app/adapters/pansou.py`: PanSou HTTP client and mapper.
- Create `backend_py/app/adapters/p115_adapter.py`: 115 Cookie transfer adapter.
- Create `backend_py/app/adapters/alist.py`: AList `/api/fs/list` adapter.
- Create `backend_py/app/services/search_service.py`: PanSou-only search orchestration and search history write.
- Create `backend_py/app/services/strm_service.py`: STRM generation ported from `since25/strm_webhook`.
- Create `backend_py/app/services/task_log_service.py`: log persistence and in-memory fanout.
- Create `backend_py/app/services/workflow_service.py`: task state machine for transfer, AList refresh, STRM generation.
- Create `backend_py/app/repositories/database.py`: SQLite connection and schema initialization.
- Create `backend_py/app/repositories/search_history_repository.py`: search history writes.
- Create `backend_py/app/repositories/task_repository.py`: task CRUD and status updates.
- Create `backend_py/app/repositories/task_log_repository.py`: task log writes and reads.
- Create `backend_py/app/api/health.py`: `/api/health`.
- Create `backend_py/app/api/search.py`: `/api/search`.
- Create `backend_py/app/api/tasks.py`: task creation, status, logs, SSE.
- Create `backend_py/app/api/strm_compat.py`: `/webhook/strm` and `/webhook/strm/direct` compatibility routes.
- Create `backend_py/scripts/p115_probe.py`: real Cookie validation script.
- Create `backend_py/tests/`: focused pytest coverage for mapping, repositories, STRM, API compatibility.
- Create `backend_py/Dockerfile`: FastAPI backend image.
- Modify `docker-compose.yml`: switch backend service to FastAPI image after backend parity.
- Modify `README.md` and docs after parity: replace CloudSaver runtime instructions with PanSou, p115, AList, STRM configuration.

## Task 1: Add Python Backend Skeleton

**Files:**
- Create: `backend_py/requirements.txt`
- Create: `backend_py/app/__init__.py`
- Create: `backend_py/app/config.py`
- Create: `backend_py/app/main.py`
- Create: `backend_py/app/api/__init__.py`
- Create: `backend_py/app/api/health.py`
- Test: `backend_py/tests/test_health.py`

- [ ] **Step 1: Add dependencies**

Create `backend_py/requirements.txt` with:

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic-settings==2.7.1
httpx==0.28.1
p115client==0.0.8.5.1.1
pytest==8.3.4
pytest-asyncio==0.25.2
```

- [ ] **Step 2: Write the failing health API test**

Create `backend_py/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_ok():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"status": "ok"}}
```

- [ ] **Step 3: Run the failing test**

Run:

```bash
cd backend_py
PYTHONPATH=. pytest tests/test_health.py -v
```

Expected: FAIL because `app.main` does not exist.

- [ ] **Step 4: Add config and app skeleton**

Create `backend_py/app/config.py`:

```python
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    port: int = Field(default=3000, alias="PORT")
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")
    database_path: Path = Field(default=Path("./data/app.db"), alias="DATABASE_PATH")

    pansou_base_url: str = Field(default="http://192.168.70.120:8888", alias="PANSOU_BASE_URL")
    pansou_search_path: str = Field(default="/api/search", alias="PANSOU_SEARCH_PATH")

    p115_cookie: str = Field(default="", alias="P115_COOKIE")
    p115_default_movie_folder: str = Field(default="automv", alias="P115_DEFAULT_MOVIE_FOLDER")
    p115_default_tv_folder: str = Field(default="autotv", alias="P115_DEFAULT_TV_FOLDER")
    p115_alist_base_path: str = Field(default="/115", alias="P115_ALIST_BASE_PATH")

    alist_url: str = Field(default="http://192.168.70.138:5244", alias="ALIST_URL")
    alist_token: str = Field(default="", alias="ALIST_TOKEN")
    strm_server: str = Field(default="http://192.168.70.138:5244/d", alias="STRM_SERVER")
    strm_save_dir: Path = Field(default=Path("/data/strm"), alias="STRM_SAVE_DIR")
    strm_replace_path: str = Field(default="", alias="STRM_REPLACE_PATH")
    strm_delay_seconds: int = Field(default=10, alias="STRM_DELAY_SECONDS")
    strm_video_exts: str = Field(default="mp4,mkv,flv,mov,m4v,avi,webm,wmv,ts,rmvb", alias="STRM_VIDEO_EXTS")

    def normalized_strm_server(self) -> str:
        value = self.strm_server
        if not value.startswith("http"):
            value = f"http://{value}"
        value = value.rstrip("/")
        return value if value.endswith("/d") else f"{value}/d"

    def video_ext_set(self) -> set[str]:
        return {item.strip().lower() for item in self.strm_video_exts.split(",") if item.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

Create `backend_py/app/api/health.py`:

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {"success": True, "data": {"status": "ok"}}
```

Create `backend_py/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="strmallinone backend")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api")
    return app


app = create_app()
```

Create empty package markers:

```text
backend_py/app/__init__.py
backend_py/app/api/__init__.py
```

- [ ] **Step 5: Run health test**

Run:

```bash
cd backend_py
PYTHONPATH=. pytest tests/test_health.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend_py
git commit -m "Add FastAPI backend skeleton" -m "Create the Python backend foundation with typed settings, CORS, and a health endpoint so later tasks can add API-compatible search and task routes." -m "Constraint: Preserve the existing /api/health response shape." -m "Tested: PYTHONPATH=. pytest tests/test_health.py -v" -m "Co-authored-by: OmX <omx@oh-my-codex.dev>"
```

## Task 2: Add SQLite Repositories And Models

**Files:**
- Create: `backend_py/app/models/resource.py`
- Create: `backend_py/app/models/task.py`
- Create: `backend_py/app/models/transfer.py`
- Create: `backend_py/app/repositories/__init__.py`
- Create: `backend_py/app/repositories/database.py`
- Create: `backend_py/app/repositories/task_repository.py`
- Create: `backend_py/app/repositories/task_log_repository.py`
- Create: `backend_py/app/repositories/search_history_repository.py`
- Test: `backend_py/tests/test_repositories.py`

- [ ] **Step 1: Write repository tests**

Create `backend_py/tests/test_repositories.py`:

```python
from pathlib import Path

from app.models.resource import ResourceDto
from app.repositories.database import Database
from app.repositories.search_history_repository import SearchHistoryRepository
from app.repositories.task_log_repository import TaskLogRepository
from app.repositories.task_repository import TaskRepository


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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd backend_py
PYTHONPATH=. pytest tests/test_repositories.py -v
```

Expected: FAIL because models and repositories do not exist.

- [ ] **Step 3: Add models**

Create `backend_py/app/models/resource.py`:

```python
from typing import Literal

from pydantic import BaseModel, Field

Provider = Literal["115"]
MediaType = Literal["movie", "tv"]


class ResourceDto(BaseModel):
    id: str
    title: str
    provider: Provider
    mediaType: MediaType
    rawType: str
    size: str
    shareUrl: str
    extra: dict[str, object] = Field(default_factory=dict)
```

Create `backend_py/app/models/task.py`:

```python
from typing import Literal

from pydantic import BaseModel

from app.models.resource import ResourceDto

StepStatus = Literal["pending", "success", "failed"]
TaskStatus = Literal["pending", "running", "success", "failed"]
LogLevel = Literal["info", "success", "error"]


class TaskDto(BaseModel):
    id: str
    keyword: str
    provider: str
    resourceTitle: str
    resource: ResourceDto
    status: TaskStatus
    transferStatus: StepStatus
    strmStatus: StepStatus
    errorMessage: str | None
    createdAt: str
    updatedAt: str


class TaskLogDto(BaseModel):
    id: int
    taskId: str
    level: LogLevel
    message: str
    createdAt: str
```

Create `backend_py/app/models/transfer.py`:

```python
from pydantic import BaseModel, Field


class TransferData(BaseModel):
    savePath: str
    sourceName: str
    savedName: str
    fileCount: int
    transferId: str
    duplicate: bool = False


class TransferResult(BaseModel):
    success: bool
    message: str
    data: TransferData | None = None
    raw: dict[str, object] = Field(default_factory=dict)
```

- [ ] **Step 4: Add repositories**

Create `backend_py/app/repositories/database.py`:

```python
import sqlite3
from pathlib import Path
from typing import Iterable


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def execute(self, sql: str, params: Iterable[object] = ()) -> sqlite3.Cursor:
        conn = self.connect()
        try:
            cur = conn.execute(sql, tuple(params))
            conn.commit()
            return cur
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
```

Create repository classes that use ISO timestamps and pydantic validation:

```python
# backend_py/app/repositories/task_repository.py
import json
from datetime import datetime, timezone

from app.models.resource import ResourceDto
from app.models.task import TaskDto, TaskStatus, StepStatus
from app.repositories.database import Database


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
```

```python
# backend_py/app/repositories/task_log_repository.py
from datetime import datetime, timezone

from app.models.task import LogLevel, TaskLogDto
from app.repositories.database import Database


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
```

```python
# backend_py/app/repositories/search_history_repository.py
from datetime import datetime, timezone

from app.repositories.database import Database


class SearchHistoryRepository:
    def __init__(self, db: Database):
        self.db = db

    def create(self, keyword: str, driver: str, result_count: int) -> None:
        self.db.execute(
            "INSERT INTO search_history (keyword, driver, result_count, created_at) VALUES (?, ?, ?, ?)",
            (keyword, driver, result_count, datetime.now(timezone.utc).isoformat()),
        )
```

Create `backend_py/app/repositories/__init__.py` as an empty file.

- [ ] **Step 5: Run repository tests**

Run:

```bash
cd backend_py
PYTHONPATH=. pytest tests/test_repositories.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend_py
git commit -m "Add FastAPI SQLite repositories" -m "Add Python models and repository classes that preserve the existing task, log, and search history data shapes for the backend migration." -m "Constraint: Keep frontend-facing task field names camelCase." -m "Tested: PYTHONPATH=. pytest tests/test_repositories.py -v" -m "Co-authored-by: OmX <omx@oh-my-codex.dev>"
```

## Task 3: Implement PanSou-Only Search

**Files:**
- Create: `backend_py/app/adapters/__init__.py`
- Create: `backend_py/app/adapters/pansou.py`
- Create: `backend_py/app/services/search_service.py`
- Create: `backend_py/app/api/search.py`
- Modify: `backend_py/app/main.py`
- Test: `backend_py/tests/test_pansou_search.py`

- [ ] **Step 1: Write PanSou mapper and API tests**

Create `backend_py/tests/test_pansou_search.py`:

```python
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.adapters.pansou import PanSouClient, map_pansou_item
from app.main import create_app
from app.repositories.database import Database
from app.repositories.search_history_repository import SearchHistoryRepository
from app.services.search_service import SearchService


def test_map_pansou_item_extracts_115_codes():
    item = {
        "name": "Example Movie",
        "url": "https://115cdn.com/s/sabc123?password=ABCD",
        "password": "",
        "datetime": "2026-01-01",
    }

    resource = map_pansou_item(item, "movie")

    assert resource is not None
    assert resource.id == "pansou_sabc123_ABCD"
    assert resource.provider == "115"
    assert resource.extra["source"] == "pansou"
    assert resource.extra["shareCode"] == "sabc123"
    assert resource.extra["receiveCode"] == "ABCD"


def test_map_pansou_item_uses_password_field():
    item = {"name": "Show", "url": "https://115.com/s/sxyz987", "password": "EFGH"}

    resource = map_pansou_item(item, "tv")

    assert resource is not None
    assert resource.extra["shareCode"] == "sxyz987"
    assert resource.extra["receiveCode"] == "EFGH"


@pytest.mark.asyncio
async def test_search_service_posts_to_pansou(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/search"
        assert json.loads(request.content) == {"kw": "movie", "cloud_types": ["115"]}
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": {
                    "merged_by_type": {
                        "115": [
                            {"name": "Movie", "url": "https://115cdn.com/s/sabc?password=ABCD", "password": ""}
                        ]
                    }
                },
            },
        )

    transport = httpx.MockTransport(handler)
    pansou = PanSouClient("http://pansou.local", "/api/search", transport=transport)
    history = SearchHistoryRepository(Database(tmp_path / "app.db"))
    service = SearchService(pansou, history)

    results = await service.search("movie", "115", "movie")

    assert len(results) == 1
    assert results[0].title == "Movie"


def test_search_api_keeps_response_shape(tmp_path, monkeypatch):
    async def fake_search(keyword: str, driver: str, media_type: str):
        assert keyword == "movie"
        assert driver == "115"
        assert media_type == "movie"
        return []

    app = create_app()
    app.state.search_service.search = fake_search
    client = TestClient(app)

    response = client.post("/api/search", json={"keyword": "movie", "driver": "115", "mediaType": "movie"})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": []}
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd backend_py
PYTHONPATH=. pytest tests/test_pansou_search.py -v
```

Expected: FAIL because PanSou modules and route do not exist.

- [ ] **Step 3: Add PanSou adapter**

Create `backend_py/app/adapters/pansou.py`:

```python
import re
from typing import Literal

import httpx

from app.models.resource import MediaType, ResourceDto

LINK_RE = re.compile(r"/s/(?P<share>[a-z0-9]+)(?:\?password=(?P<pwd>[A-Za-z0-9]{4}))?", re.I)


def parse_115_link(url: str, password: str | None = None) -> tuple[str, str] | None:
    match = LINK_RE.search(url)
    receive_code = password or (match.group("pwd") if match else None)
    if not match or not receive_code:
        return None
    return match.group("share"), receive_code


def map_pansou_item(item: dict[str, object], media_type: MediaType) -> ResourceDto | None:
    url = str(item.get("url") or "")
    if "115" not in url:
        return None
    parsed = parse_115_link(url, str(item.get("password") or "") or None)
    if not parsed:
        return None
    share_code, receive_code = parsed
    title = str(item.get("name") or item.get("title") or share_code)
    return ResourceDto(
        id=f"pansou_{share_code}_{receive_code}",
        title=title,
        provider="115",
        mediaType=media_type,
        rawType="video",
        size=str(item.get("size") or "-"),
        shareUrl=url,
        extra={
            "source": "pansou",
            "shareCode": share_code,
            "receiveCode": receive_code,
            "raw": item,
        },
    )


class PanSouClient:
    def __init__(
        self,
        base_url: str,
        search_path: str,
        transport: httpx.AsyncBaseTransport | httpx.BaseTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.search_path = search_path
        self.transport = transport

    async def search(self, keyword: str, media_type: MediaType) -> list[ResourceDto]:
        async with httpx.AsyncClient(base_url=self.base_url, transport=self.transport, timeout=30) as client:
            response = await client.post(self.search_path, json={"kw": keyword, "cloud_types": ["115"]})
            response.raise_for_status()
            payload = response.json()
        items = payload.get("data", {}).get("merged_by_type", {}).get("115", [])
        return [
            resource
            for item in items
            if isinstance(item, dict)
            for resource in [map_pansou_item(item, media_type)]
            if resource is not None
        ]
```

- [ ] **Step 4: Add search service and route**

Create `backend_py/app/services/search_service.py`:

```python
from app.adapters.pansou import PanSouClient
from app.models.resource import MediaType, ResourceDto
from app.repositories.search_history_repository import SearchHistoryRepository


class SearchService:
    def __init__(self, pansou: PanSouClient, history: SearchHistoryRepository):
        self.pansou = pansou
        self.history = history

    async def search(self, keyword: str, driver: str, media_type: MediaType) -> list[ResourceDto]:
        resources = await self.pansou.search(keyword, media_type)
        self.history.create(keyword=keyword, driver=driver, result_count=len(resources))
        return resources
```

Create `backend_py/app/api/search.py`:

```python
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.models.resource import MediaType

router = APIRouter()


class SearchRequest(BaseModel):
    keyword: str = Field(min_length=1)
    driver: Literal["115"] = "115"
    mediaType: MediaType = "movie"


@router.post("/search")
async def search(payload: SearchRequest, request: Request):
    data = await request.app.state.search_service.search(payload.keyword.strip(), payload.driver, payload.mediaType)
    return {"success": True, "data": [item.model_dump() for item in data]}
```

Modify `backend_py/app/main.py` to initialize and mount search:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, search
from app.adapters.pansou import PanSouClient
from app.config import get_settings
from app.repositories.database import Database
from app.repositories.search_history_repository import SearchHistoryRepository
from app.services.search_service import SearchService


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="strmallinone backend")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    db = Database(settings.database_path)
    app.state.search_service = SearchService(
        PanSouClient(settings.pansou_base_url, settings.pansou_search_path),
        SearchHistoryRepository(db),
    )
    app.include_router(health.router, prefix="/api")
    app.include_router(search.router, prefix="/api")
    return app


app = create_app()
```

Create `backend_py/app/adapters/__init__.py` as an empty file.

- [ ] **Step 5: Run PanSou tests**

Run:

```bash
cd backend_py
PYTHONPATH=. pytest tests/test_pansou_search.py tests/test_health.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend_py
git commit -m "Add PanSou-only FastAPI search" -m "Implement the new backend search path using PanSou as the sole search source while preserving the existing frontend request and response shape." -m "Constraint: Do not call CloudSaver for search." -m "Tested: PYTHONPATH=. pytest tests/test_pansou_search.py tests/test_health.py -v" -m "Co-authored-by: OmX <omx@oh-my-codex.dev>"
```

## Task 4: Validate p115 With A Real Cookie

**Files:**
- Create: `backend_py/scripts/p115_probe.py`
- Test: manual command with `P115_COOKIE`, `P115_SHARE_CODE`, and `P115_RECEIVE_CODE`

- [ ] **Step 1: Add the p115 probe script**

Create `backend_py/scripts/p115_probe.py`:

```python
import json
import os
import sys
from uuid import uuid4

from p115client import P115Client


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def response_ok(resp: dict) -> bool:
    return bool(resp.get("state") is True or resp.get("code") in {0, 200} or resp.get("errno") in {0, None})


def list_children(client: P115Client, cid: int | str) -> list[dict]:
    resp = client.fs_files({"cid": cid, "limit": 1150, "offset": 0, "show_dir": 1})
    data = resp.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data") or data.get("list") or []
    return []


def ensure_folder(client: P115Client, parent_id: int, folder_name: str) -> int:
    for item in list_children(client, parent_id):
        name = item.get("n") or item.get("name") or item.get("file_name")
        file_id = item.get("fid") or item.get("cid") or item.get("file_id")
        is_dir = item.get("is_dir") or item.get("fc") == "0" or item.get("ico") == "folder"
        if name == folder_name and file_id and is_dir:
            return int(file_id)
    resp = client.fs_mkdir(folder_name, pid=parent_id)
    if not response_ok(resp):
        raise RuntimeError(f"fs_mkdir failed: {resp}")
    folder_id = resp.get("id") or resp.get("cid") or resp.get("file_id") or resp.get("data", {}).get("file_id")
    if not folder_id:
        raise RuntimeError(f"fs_mkdir returned no folder id: {resp}")
    return int(folder_id)


def first_share_file(client: P115Client, share_code: str, receive_code: str) -> dict:
    resp = client.share_snap({"share_code": share_code, "receive_code": receive_code, "cid": 0, "limit": 32})
    if not response_ok(resp):
        raise RuntimeError(f"share_snap failed: {resp}")
    data = resp.get("data") or {}
    items = data.get("list") or data.get("data") or []
    if not items:
        raise RuntimeError(f"share contains no files: {resp}")
    return items[0]


def main() -> int:
    cookie = require_env("P115_COOKIE")
    share_code = require_env("P115_SHARE_CODE")
    receive_code = require_env("P115_RECEIVE_CODE")
    target_parent_id = int(os.environ.get("P115_TARGET_PARENT_ID", "0"))
    target_folder_name = os.environ.get("P115_PROBE_FOLDER", f"strmallinone_probe_{uuid4().hex[:8]}")

    client = P115Client(cookie)
    target_cid = ensure_folder(client, target_parent_id, target_folder_name)
    share_file = first_share_file(client, share_code, receive_code)
    file_id = share_file.get("fid") or share_file.get("cid") or share_file.get("file_id")
    file_name = share_file.get("n") or share_file.get("name") or share_file.get("file_name") or str(file_id)
    if not file_id:
        raise RuntimeError(f"share file has no id: {share_file}")

    receive_resp = client.share_receive(
        {
            "share_code": share_code,
            "receive_code": receive_code,
            "file_id": str(file_id),
            "cid": str(target_cid),
            "is_check": 0,
        }
    )
    if not response_ok(receive_resp):
        raise RuntimeError(f"share_receive failed: {receive_resp}")

    print(
        json.dumps(
            {
                "success": True,
                "targetCid": target_cid,
                "targetFolder": target_folder_name,
                "fileId": str(file_id),
                "fileName": file_name,
                "receiveResponse": receive_resp,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run the script without env to verify validation**

Run:

```bash
cd backend_py
PYTHONPATH=. python scripts/p115_probe.py
```

Expected: FAIL with `Missing required environment variable: P115_COOKIE`.

- [ ] **Step 3: Run the real Cookie validation**

Run with a known small 115 share:

```bash
cd backend_py
P115_COOKIE='...' P115_SHARE_CODE='...' P115_RECEIVE_CODE='....' PYTHONPATH=. python scripts/p115_probe.py
```

Expected: JSON output with `"success": true`, `targetCid`, `fileId`, and `receiveResponse`.

- [ ] **Step 4: Commit after real validation succeeds**

```bash
git add backend_py/scripts/p115_probe.py backend_py/requirements.txt
git commit -m "Add p115 transfer validation probe" -m "Add a focused script that proves p115client can authenticate with a Cookie, read a share, create or find a target folder, and receive a shared file before the full backend migration proceeds." -m "Constraint: Stop migration if the probe cannot complete with a real Cookie." -m "Tested: P115_COOKIE and known share validation completed successfully." -m "Co-authored-by: OmX <omx@oh-my-codex.dev>"
```

## Task 5: Implement p115 Transfer Adapter

**Files:**
- Create: `backend_py/app/adapters/p115_adapter.py`
- Test: `backend_py/tests/test_p115_adapter.py`

- [ ] **Step 1: Write mocked p115 adapter tests**

Create `backend_py/tests/test_p115_adapter.py`:

```python
from app.adapters.p115_adapter import P115TransferAdapter
from app.models.resource import ResourceDto


class FakeClient:
    def __init__(self, cookie: str):
        self.cookie = cookie
        self.received_payload = None

    def fs_files(self, payload):
        return {"state": True, "data": [{"name": "automv", "cid": "100", "is_dir": True}]}

    def share_snap(self, payload):
        return {"state": True, "data": {"list": [{"file_id": "200", "file_name": "Movie Folder", "is_dir": True}]}}

    def share_receive(self, payload):
        self.received_payload = payload
        return {"state": True, "message": "ok"}


def test_transfer_receives_share_into_movie_folder():
    resource = ResourceDto(
        id="pansou_sabc_ABCD",
        title="Movie Folder",
        provider="115",
        mediaType="movie",
        rawType="video",
        size="-",
        shareUrl="https://115cdn.com/s/sabc?password=ABCD",
        extra={"shareCode": "sabc", "receiveCode": "ABCD"},
    )
    client = FakeClient("cookie")
    adapter = P115TransferAdapter(
        cookie="cookie",
        default_movie_folder="automv",
        default_tv_folder="autotv",
        alist_base_path="/115",
        client_factory=lambda cookie: client,
    )

    result = adapter.transfer(resource)

    assert result.success is True
    assert result.data is not None
    assert result.data.savePath == "/115/automv/Movie Folder"
    assert client.received_payload == {
        "share_code": "sabc",
        "receive_code": "ABCD",
        "file_id": "200",
        "cid": "100",
        "is_check": 0,
    }
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd backend_py
PYTHONPATH=. pytest tests/test_p115_adapter.py -v
```

Expected: FAIL because `P115TransferAdapter` does not exist.

- [ ] **Step 3: Implement adapter**

Create `backend_py/app/adapters/p115_adapter.py` with:

```python
from collections.abc import Callable
from uuid import uuid4

from p115client import P115Client

from app.models.resource import ResourceDto
from app.models.transfer import TransferData, TransferResult


def ok_response(resp: dict) -> bool:
    message = str(resp.get("message") or "")
    return bool(resp.get("state") is True or resp.get("code") in {0, 200} or "已接收" in message or "无需重复" in message)


def item_name(item: dict) -> str:
    return str(item.get("file_name") or item.get("name") or item.get("n") or "")


def item_id(item: dict) -> str:
    value = item.get("file_id") or item.get("fid") or item.get("cid")
    return str(value or "")


class P115TransferAdapter:
    def __init__(
        self,
        cookie: str,
        default_movie_folder: str,
        default_tv_folder: str,
        alist_base_path: str,
        client_factory: Callable[[str], object] = P115Client,
    ):
        self.cookie = cookie
        self.default_movie_folder = default_movie_folder
        self.default_tv_folder = default_tv_folder
        self.alist_base_path = alist_base_path.rstrip("/")
        self.client = client_factory(cookie)

    def target_folder_name(self, resource: ResourceDto) -> str:
        return self.default_tv_folder if resource.mediaType == "tv" else self.default_movie_folder

    def find_target_folder(self, folder_name: str) -> str:
        resp = self.client.fs_files({"cid": 0, "limit": 1150, "offset": 0, "show_dir": 1})
        children = resp.get("data", [])
        if isinstance(children, dict):
            children = children.get("data") or children.get("list") or []
        for item in children:
            if item_name(item) == folder_name:
                folder_id = item_id(item)
                if folder_id:
                    return folder_id
        raise RuntimeError(f"未找到目标目录: {folder_name}")

    def first_share_file(self, share_code: str, receive_code: str) -> dict:
        resp = self.client.share_snap({"share_code": share_code, "receive_code": receive_code, "cid": 0, "limit": 32})
        if not ok_response(resp):
            raise RuntimeError(str(resp.get("message") or "读取 115 分享失败"))
        data = resp.get("data") or {}
        items = data.get("list") or data.get("data") or []
        if not items:
            raise RuntimeError("分享链接为空，未获取到可转存文件")
        return items[0]

    def transfer(self, resource: ResourceDto) -> TransferResult:
        share_code = str(resource.extra.get("shareCode") or "")
        receive_code = str(resource.extra.get("receiveCode") or "")
        if not share_code or not receive_code:
            return TransferResult(success=False, message="资源缺少 115 shareCode 或 receiveCode")

        folder_name = self.target_folder_name(resource)
        target_cid = self.find_target_folder(folder_name)
        primary = self.first_share_file(share_code, receive_code)
        file_id = item_id(primary)
        source_name = item_name(primary) or resource.title
        if not file_id:
            return TransferResult(success=False, message="分享文件缺少 file_id", raw={"shareFile": primary})

        receive_resp = self.client.share_receive(
            {
                "share_code": share_code,
                "receive_code": receive_code,
                "file_id": file_id,
                "cid": target_cid,
                "is_check": 0,
            }
        )
        duplicate = "已接收" in str(receive_resp.get("message") or "") or "无需重复" in str(receive_resp.get("message") or "")
        if not ok_response(receive_resp):
            return TransferResult(success=False, message=str(receive_resp.get("message") or "115 转存失败"), raw=receive_resp)

        return TransferResult(
            success=True,
            message="115 文件已存在，跳过重复接收" if duplicate else "115 转存成功",
            data=TransferData(
                savePath=f"{self.alist_base_path}/{folder_name}/{source_name}",
                sourceName=source_name,
                savedName=source_name,
                fileCount=1,
                transferId=uuid4().hex,
                duplicate=duplicate,
            ),
            raw={"receiveResponse": receive_resp, "shareFile": primary},
        )
```

- [ ] **Step 4: Run adapter tests**

Run:

```bash
cd backend_py
PYTHONPATH=. pytest tests/test_p115_adapter.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend_py
git commit -m "Add p115 transfer adapter" -m "Implement the direct 115 transfer adapter around p115client so the backend can receive PanSou 115 shares without CloudSaver." -m "Constraint: Return the existing normalized transfer result shape." -m "Tested: PYTHONPATH=. pytest tests/test_p115_adapter.py -v" -m "Co-authored-by: OmX <omx@oh-my-codex.dev>"
```

## Task 6: Port AList And STRM Generation

**Files:**
- Create: `backend_py/app/adapters/alist.py`
- Create: `backend_py/app/services/strm_service.py`
- Test: `backend_py/tests/test_strm_service.py`

- [ ] **Step 1: Write STRM service tests**

Create `backend_py/tests/test_strm_service.py`:

```python
from pathlib import Path

from app.services.strm_service import StrmConfig, StrmService


class FakeAList:
    def __init__(self):
        self.tree = {
            "/115": [{"name": "automv", "is_dir": True}],
            "/115/automv": [{"name": "Movie Folder", "is_dir": True}],
            "/115/automv/Movie Folder": [
                {"name": "Movie.mkv", "is_dir": False},
                {"name": "poster.jpg", "is_dir": False},
            ],
        }

    def list_dir(self, path: str, refresh: bool = False):
        return self.tree.get(path)


def test_generate_for_path_writes_video_strm(tmp_path: Path):
    service = StrmService(
        FakeAList(),
        StrmConfig(
            strm_server="http://alist.local/d",
            strm_save_dir=tmp_path,
            strm_replace_path="",
            video_exts={"mkv"},
        ),
    )

    result = service.generate_for_path("/115/automv/Movie Folder")

    output = tmp_path / "115" / "automv" / "Movie Folder" / "Movie.strm"
    assert output.read_text() == "http://alist.local/d/115/automv/Movie%20Folder/Movie.mkv"
    assert result["created"] == [str(output)]
    assert result["skipped"] == []
    assert result["errors"] == []


def test_direct_files_skip_existing(tmp_path: Path):
    output = tmp_path / "115" / "automv" / "Movie.strm"
    output.parent.mkdir(parents=True)
    output.write_text("old")
    service = StrmService(
        FakeAList(),
        StrmConfig("http://alist.local/d", tmp_path, "", {"mkv"}),
    )

    result = service.generate_direct(["/115/automv/Movie.mkv"])

    assert result["created"] == []
    assert result["skipped"] == [str(output)]
    assert output.read_text() == "old"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd backend_py
PYTHONPATH=. pytest tests/test_strm_service.py -v
```

Expected: FAIL because STRM service does not exist.

- [ ] **Step 3: Add AList adapter**

Create `backend_py/app/adapters/alist.py`:

```python
import httpx


class AListClient:
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": token} if token else {}

    def list_dir(self, path: str, refresh: bool = False) -> list[dict] | None:
        response = httpx.post(
            f"{self.base_url}/api/fs/list",
            headers=self.headers,
            json={"path": path, "refresh": refresh, "password": "", "page": 1, "per_page": 0},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != 200:
            return None
        return payload.get("data", {}).get("content") or []
```

- [ ] **Step 4: Add STRM service**

Create `backend_py/app/services/strm_service.py`:

```python
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote


@dataclass(frozen=True)
class StrmConfig:
    strm_server: str
    strm_save_dir: Path
    strm_replace_path: str
    video_exts: set[str]


class StrmService:
    def __init__(self, alist, config: StrmConfig):
        self.alist = alist
        self.config = config

    def generate_for_path(self, alist_path: str) -> dict[str, list[str]]:
        result = {"created": [], "skipped": [], "errors": []}
        actual_path = self.resolve_actual_path(alist_path)
        if not actual_path:
            result["errors"].append(f"解析路径失败: {alist_path}")
            return result
        items = self.alist.list_dir(actual_path, refresh=True)
        if items is None:
            result["errors"].append(f"无法列出目录: {actual_path}")
            return result
        self.process_items(actual_path, items, result)
        return result

    def generate_direct(self, files: list[str]) -> dict[str, list[str]]:
        result = {"created": [], "skipped": [], "errors": []}
        for file_path in files:
            self.process_file(file_path if file_path.startswith("/") else f"/{file_path}", result)
        return result

    def resolve_actual_path(self, target_path: str) -> str | None:
        segments = target_path.strip("/").split("/") if target_path.strip("/") else []
        current = ""
        index = 0
        while index < len(segments):
            parent = current or "/"
            items = self.alist.list_dir(parent, refresh=True)
            if items is None:
                return None
            matched = None
            consumed = 0
            for count in range(len(segments) - index, 0, -1):
                candidate = "/".join(segments[index : index + count])
                matched = self.find_item(candidate, items)
                if matched:
                    consumed = count
                    break
            if not matched:
                return None
            current = f"{current}/{matched}".replace("//", "/")
            index += consumed
        return current or "/"

    def find_item(self, target_name: str, items: list[dict]) -> str | None:
        def normalize(value: str) -> str:
            normalized = value.strip().lower()
            for char in ["/", "|", "／", "\\", " "]:
                normalized = normalized.replace(char, "")
            return normalized

        for item in items:
            name = str(item.get("name", ""))
            if name == target_name:
                return name
        target = normalize(target_name)
        for item in items:
            name = str(item.get("name", ""))
            if normalize(name) == target:
                return name
        return None

    def process_items(self, dir_path: str, items: list[dict], result: dict[str, list[str]]) -> None:
        for item in items:
            name = str(item.get("name", ""))
            item_path = f"{dir_path}/{name}".replace("//", "/")
            if item.get("is_dir"):
                child_items = self.alist.list_dir(item_path, refresh=False)
                if child_items is None:
                    result["errors"].append(f"无法列出目录: {item_path}")
                    continue
                self.process_items(item_path, child_items, result)
            else:
                self.process_file(item_path, result)

    def process_file(self, file_path: str, result: dict[str, list[str]]) -> None:
        ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
        if ext not in self.config.video_exts:
            return
        strm_path = Path(file_path).with_suffix(".strm")
        full_path = self.config.strm_save_dir / str(strm_path).lstrip("/")
        if full_path.exists():
            result["skipped"].append(str(full_path))
            return
        full_path.parent.mkdir(parents=True, exist_ok=True)
        strm_file_path = file_path
        if self.config.strm_replace_path:
            parts = file_path.split("/", 2)
            if len(parts) >= 3:
                strm_file_path = f"{self.config.strm_replace_path}/{parts[2]}"
        content = f"{self.config.strm_server.rstrip('/')}{quote(strm_file_path, safe='/')}"
        full_path.write_text(content, encoding="utf-8")
        result["created"].append(str(full_path))
```

- [ ] **Step 5: Run STRM tests**

Run:

```bash
cd backend_py
PYTHONPATH=. pytest tests/test_strm_service.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend_py
git commit -m "Port STRM generation into FastAPI backend" -m "Add the AList adapter and STRM service so the new backend can refresh AList-visible paths and generate Emby-ready STRM files internally." -m "Constraint: Preserve direct-file and recursive directory behavior from strm_webhook." -m "Tested: PYTHONPATH=. pytest tests/test_strm_service.py -v" -m "Co-authored-by: OmX <omx@oh-my-codex.dev>"
```

## Task 7: Add Task API, Logs, SSE, And Workflow

**Files:**
- Create: `backend_py/app/services/task_log_service.py`
- Create: `backend_py/app/services/workflow_service.py`
- Create: `backend_py/app/api/tasks.py`
- Modify: `backend_py/app/main.py`
- Test: `backend_py/tests/test_tasks_api.py`

- [ ] **Step 1: Write task API test**

Create `backend_py/tests/test_tasks_api.py`:

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_create_transfer_task_returns_task_id(monkeypatch):
    app = create_app()

    async def fake_run(task_id, resource):
        app.state.task_log_service.append(task_id, "success", "fake workflow done")

    app.state.workflow_service.run = fake_run
    client = TestClient(app)
    payload = {
        "keyword": "movie",
        "resource": {
            "id": "pansou_sabc_ABCD",
            "title": "Movie",
            "provider": "115",
            "mediaType": "movie",
            "rawType": "video",
            "size": "-",
            "shareUrl": "https://115cdn.com/s/sabc?password=ABCD",
            "extra": {"shareCode": "sabc", "receiveCode": "ABCD"},
        },
    }

    response = client.post("/api/tasks/transfer", json=payload)

    assert response.status_code == 201
    task_id = response.json()["data"]["taskId"]
    task_response = client.get(f"/api/tasks/{task_id}")
    assert task_response.status_code == 200
    assert task_response.json()["data"]["resourceTitle"] == "Movie"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd backend_py
PYTHONPATH=. pytest tests/test_tasks_api.py -v
```

Expected: FAIL because task route and services do not exist.

- [ ] **Step 3: Add log and workflow services**

Create `backend_py/app/services/task_log_service.py`:

```python
import asyncio

from app.models.task import LogLevel, TaskLogDto
from app.repositories.task_log_repository import TaskLogRepository


class TaskLogService:
    def __init__(self, repository: TaskLogRepository):
        self.repository = repository
        self.queues: dict[str, set[asyncio.Queue[TaskLogDto]]] = {}

    def append(self, task_id: str, level: LogLevel, message: str) -> TaskLogDto:
        row = self.repository.append(task_id, level, message)
        for queue in self.queues.get(task_id, set()):
            queue.put_nowait(row)
        return row

    def list_by_task(self, task_id: str) -> list[TaskLogDto]:
        return self.repository.list_by_task(task_id)

    def subscribe(self, task_id: str) -> asyncio.Queue[TaskLogDto]:
        queue: asyncio.Queue[TaskLogDto] = asyncio.Queue()
        self.queues.setdefault(task_id, set()).add(queue)
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue[TaskLogDto]) -> None:
        self.queues.get(task_id, set()).discard(queue)
```

Create `backend_py/app/services/workflow_service.py`:

```python
import asyncio

from app.models.resource import ResourceDto
from app.repositories.task_repository import TaskRepository
from app.services.task_log_service import TaskLogService


class WorkflowService:
    def __init__(self, tasks: TaskRepository, logs: TaskLogService, transfer_adapter, strm_service, strm_delay_seconds: int):
        self.tasks = tasks
        self.logs = logs
        self.transfer_adapter = transfer_adapter
        self.strm_service = strm_service
        self.strm_delay_seconds = strm_delay_seconds

    async def run(self, task_id: str, resource: ResourceDto) -> None:
        self.tasks.update_statuses(task_id, "running", "pending", "pending")
        self.logs.append(task_id, "info", "任务开始")
        self.logs.append(task_id, "info", "开始调用 p115 进行 115 转存")
        try:
            transfer = await asyncio.to_thread(self.transfer_adapter.transfer, resource)
            if not transfer.success or not transfer.data:
                self.tasks.update_statuses(task_id, "failed", "failed", "pending", transfer.message)
                self.logs.append(task_id, "error", transfer.message)
                return
            self.tasks.update_statuses(task_id, "running", "success", "pending")
            self.logs.append(task_id, "success", f"115 转存成功: {transfer.data.savePath}")
            self.logs.append(task_id, "info", f"等待 AList 刷新: {self.strm_delay_seconds} 秒")
            await asyncio.sleep(self.strm_delay_seconds)
            self.logs.append(task_id, "info", "开始生成 STRM")
            result = await asyncio.to_thread(self.strm_service.generate_for_path, transfer.data.savePath)
            if result["errors"]:
                message = result["errors"][0]
                self.tasks.update_statuses(task_id, "failed", "success", "failed", message)
                self.logs.append(task_id, "error", message)
                return
            self.tasks.update_statuses(task_id, "success", "success", "success")
            self.logs.append(
                task_id,
                "success",
                f"STRM 生成完成: 新建={len(result['created'])}, 跳过={len(result['skipped'])}",
            )
            self.logs.append(task_id, "success", "任务完成")
        except Exception as exc:
            message = str(exc)
            self.tasks.update_statuses(task_id, "failed", "failed", "failed", message)
            self.logs.append(task_id, "error", f"任务异常: {message}")
```

- [ ] **Step 4: Add task routes and wire app state**

Create `backend_py/app/api/tasks.py`:

```python
import asyncio
import json
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models.resource import ResourceDto

router = APIRouter()


class CreateTaskRequest(BaseModel):
    keyword: str
    resource: ResourceDto


@router.post("/tasks/transfer", status_code=201)
async def create_transfer_task(payload: CreateTaskRequest, request: Request):
    task_id = f"task_{uuid4().hex[:10]}"
    request.app.state.task_repository.create(task_id, payload.keyword, payload.resource)
    request.app.state.task_log_service.append(task_id, "info", "任务已创建，等待执行")
    asyncio.create_task(request.app.state.workflow_service.run(task_id, payload.resource))
    return {"success": True, "data": {"taskId": task_id}}


@router.get("/tasks/{task_id}")
def get_task(task_id: str, request: Request):
    task = request.app.state.task_repository.find_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return {"success": True, "data": task.model_dump()}


@router.get("/tasks/{task_id}/logs")
def get_logs(task_id: str, request: Request):
    logs = request.app.state.task_log_service.list_by_task(task_id)
    return {"success": True, "data": [row.model_dump() for row in logs]}


@router.get("/tasks/{task_id}/logs/stream")
async def stream_logs(task_id: str, request: Request):
    service = request.app.state.task_log_service
    queue = service.subscribe(task_id)

    async def events():
        try:
            for row in service.list_by_task(task_id):
                yield f"event: log\\ndata: {json.dumps(row.model_dump(), ensure_ascii=False)}\\n\\n"
            while True:
                row = await queue.get()
                yield f"event: log\\ndata: {json.dumps(row.model_dump(), ensure_ascii=False)}\\n\\n"
        finally:
            service.unsubscribe(task_id, queue)

    return StreamingResponse(events(), media_type="text/event-stream")
```

Modify `backend_py/app/main.py` to initialize task dependencies and mount routes:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, search, tasks
from app.adapters.alist import AListClient
from app.adapters.p115_adapter import P115TransferAdapter
from app.adapters.pansou import PanSouClient
from app.config import get_settings
from app.repositories.database import Database
from app.repositories.search_history_repository import SearchHistoryRepository
from app.repositories.task_log_repository import TaskLogRepository
from app.repositories.task_repository import TaskRepository
from app.services.search_service import SearchService
from app.services.strm_service import StrmConfig, StrmService
from app.services.task_log_service import TaskLogService
from app.services.workflow_service import WorkflowService


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="strmallinone backend")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    db = Database(settings.database_path)
    task_repository = TaskRepository(db)
    task_log_service = TaskLogService(TaskLogRepository(db))
    strm_service = StrmService(
        AListClient(settings.alist_url, settings.alist_token),
        StrmConfig(
            strm_server=settings.normalized_strm_server(),
            strm_save_dir=settings.strm_save_dir,
            strm_replace_path=settings.strm_replace_path,
            video_exts=settings.video_ext_set(),
        ),
    )

    app.state.search_service = SearchService(
        PanSouClient(settings.pansou_base_url, settings.pansou_search_path),
        SearchHistoryRepository(db),
    )
    app.state.task_repository = task_repository
    app.state.task_log_service = task_log_service
    app.state.strm_service = strm_service
    app.state.workflow_service = WorkflowService(
        task_repository,
        task_log_service,
        P115TransferAdapter(
            cookie=settings.p115_cookie,
            default_movie_folder=settings.p115_default_movie_folder,
            default_tv_folder=settings.p115_default_tv_folder,
            alist_base_path=settings.p115_alist_base_path,
        ),
        strm_service,
        settings.strm_delay_seconds,
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(search.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")
    return app


app = create_app()
```

- [ ] **Step 5: Run task API test**

Run:

```bash
cd backend_py
PYTHONPATH=. pytest tests/test_tasks_api.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend_py
git commit -m "Add FastAPI task workflow routes" -m "Add task creation, task reads, log reads, SSE streaming, and the p115 to AList to STRM workflow while preserving the existing frontend API contract." -m "Constraint: Keep route paths and response envelopes compatible with the current frontend." -m "Tested: PYTHONPATH=. pytest tests/test_tasks_api.py -v" -m "Co-authored-by: OmX <omx@oh-my-codex.dev>"
```

## Task 8: Add STRM Compatibility Routes

**Files:**
- Create: `backend_py/app/api/strm_compat.py`
- Modify: `backend_py/app/main.py`
- Test: `backend_py/tests/test_strm_compat.py`

- [ ] **Step 1: Write compatibility route tests**

Create `backend_py/tests/test_strm_compat.py`:

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_webhook_strm_compat_response_shape():
    app = create_app()
    app.state.strm_service.generate_for_path = lambda path: {"created": ["a"], "skipped": [], "errors": []}
    client = TestClient(app)

    response = client.post("/webhook/strm", json={"path": "/115/automv/Movie"})

    assert response.status_code == 200
    assert response.json()["created_count"] == 1
    assert response.json()["error_count"] == 0


def test_webhook_strm_direct_response_shape():
    app = create_app()
    app.state.strm_service.generate_direct = lambda files: {"created": [], "skipped": ["a"], "errors": []}
    client = TestClient(app)

    response = client.post("/webhook/strm/direct", json={"files": ["/115/automv/Movie.mkv"]})

    assert response.status_code == 200
    assert response.json()["skipped_count"] == 1
```

- [ ] **Step 2: Implement compatibility routes**

Create `backend_py/app/api/strm_compat.py`:

```python
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class StrmPathRequest(BaseModel):
    path: str | None = None
    full_path: str | None = None
    folder_name: str | None = None
    savepath: str | None = None


class StrmDirectRequest(BaseModel):
    files: list[str]


def summarize(message: str, path: str | None, result: dict[str, list[str]]):
    return {
        "code": 200,
        "message": message,
        "path": path,
        "created_count": len(result["created"]),
        "skipped_count": len(result["skipped"]),
        "error_count": len(result["errors"]),
        "details": result,
    }


@router.post("/webhook/strm")
def webhook_strm(payload: StrmPathRequest, request: Request):
    path = payload.path or payload.full_path or payload.folder_name or payload.savepath
    if not path:
        raise HTTPException(status_code=400, detail="缺少 path 参数")
    if not path.startswith("/"):
        path = f"/{path}"
    result = request.app.state.strm_service.generate_for_path(path)
    return summarize("STRM 生成完成", path, result)


@router.post("/webhook/strm/direct")
def webhook_strm_direct(payload: StrmDirectRequest, request: Request):
    if not payload.files:
        raise HTTPException(status_code=400, detail="缺少 files 参数")
    result = request.app.state.strm_service.generate_direct(payload.files)
    return summarize("STRM 直传生成完成", None, result)
```

Mount this router in `backend_py/app/main.py` without an `/api` prefix.

- [ ] **Step 3: Run compatibility tests**

Run:

```bash
cd backend_py
PYTHONPATH=. pytest tests/test_strm_compat.py -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add backend_py
git commit -m "Add STRM webhook compatibility routes" -m "Expose the old strm_webhook route shapes from FastAPI so manual calls and migration checks can continue after the Flask service is folded into the backend." -m "Constraint: Preserve /webhook/strm and /webhook/strm/direct response counters." -m "Tested: PYTHONPATH=. pytest tests/test_strm_compat.py -v" -m "Co-authored-by: OmX <omx@oh-my-codex.dev>"
```

## Task 9: Switch Docker To FastAPI Backend

**Files:**
- Create: `backend_py/Dockerfile`
- Create: `backend_py/.env.example`
- Modify: `docker-compose.yml`
- Modify: `frontend/nginx.conf` only if the upstream name or port changes

- [ ] **Step 1: Add backend Dockerfile**

Create `backend_py/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app/backend_py

ENV PYTHONPATH=/app/backend_py

COPY backend_py/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend_py ./ 

EXPOSE 3000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
```

- [ ] **Step 2: Add Python backend env example**

Create `backend_py/.env.example`:

```env
PORT=3000
FRONTEND_ORIGIN=http://localhost:8080
DATABASE_PATH=/app/backend_py/data/app.db

PANSOU_BASE_URL=http://192.168.70.120:8888
PANSOU_SEARCH_PATH=/api/search

P115_COOKIE=
P115_DEFAULT_MOVIE_FOLDER=automv
P115_DEFAULT_TV_FOLDER=autotv
P115_ALIST_BASE_PATH=/115

ALIST_URL=http://192.168.70.138:5244
ALIST_TOKEN=
STRM_SERVER=http://192.168.70.138:5244/d
STRM_SAVE_DIR=/data/strm
STRM_REPLACE_PATH=
STRM_DELAY_SECONDS=10
STRM_VIDEO_EXTS=mp4,mkv,flv,mov,m4v,avi,webm,wmv,ts,rmvb
```

- [ ] **Step 3: Modify Docker Compose backend service**

Change `docker-compose.yml` backend service to:

```yaml
  backend:
    build:
      context: .
      dockerfile: backend_py/Dockerfile
    container_name: strmallinone-backend
    restart: unless-stopped
    env_file:
      - ./backend_py/.env
    environment:
      PORT: 3000
      FRONTEND_ORIGIN: http://localhost:8080
    volumes:
      - ./backend_py/data:/app/backend_py/data
      - ./strm_output:/data/strm
    ports:
      - "3000:3000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:3000/api/health', timeout=5)"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 20s
```

- [ ] **Step 4: Build Docker images**

Run:

```bash
docker compose build backend frontend
```

Expected: both images build successfully.

- [ ] **Step 5: Commit**

```bash
git add backend_py docker-compose.yml
git commit -m "Switch Docker backend to FastAPI" -m "Update the container runtime so the backend service builds and runs the new FastAPI application while preserving the frontend and reverse proxy layout." -m "Constraint: Keep backend exposed on port 3000 for nginx and local checks." -m "Tested: docker compose build backend frontend" -m "Co-authored-by: OmX <omx@oh-my-codex.dev>"
```

## Task 10: Remove CloudSaver Runtime References And Update Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/development-guide.md`
- Delete or archive after parity: `backend/src/adapters/cloudsaver/*`
- Keep during migration if needed: existing Node backend source until deployment is verified

- [ ] **Step 1: Search remaining CloudSaver references**

Run:

```bash
rg -n "CloudSaver|cloudsaver|CLOUDSAVER" README.md docs backend backend_py docker-compose.yml
```

Expected: matches remain before docs cleanup.

- [ ] **Step 2: Update README runtime description**

Replace CloudSaver sections with:

```markdown
## Runtime Dependencies

- PanSou provides 115 search results.
- p115client receives 115 shares using `P115_COOKIE`.
- AList remains required because generated STRM files point to AList `/d` URLs and Emby plays through AList 302 redirects.
- Built-in STRM generation replaces the old standalone `since25/strm_webhook` service.
```

Add the env list from `backend_py/.env.example`.

- [ ] **Step 3: Update development guide**

Change the architecture text to describe:

```text
search -> p115 transfer -> AList refresh -> STRM generation
```

Remove instructions that tell agents to call CloudSaver adapters.

- [ ] **Step 4: Verify no runtime CloudSaver references remain**

Run:

```bash
rg -n "CloudSaver|cloudsaver|CLOUDSAVER" backend_py docker-compose.yml README.md docs
```

Expected: only historical migration notes remain in `docs/superpowers/specs` and `docs/superpowers/plans`, or no matches outside those files.

- [ ] **Step 5: Run full verification**

Run:

```bash
cd backend_py
PYTHONPATH=. pytest -v
```

Then run:

```bash
npm run build
```

Expected: backend tests pass and frontend build passes.

- [ ] **Step 6: Commit**

```bash
git add README.md docs backend_py docker-compose.yml
git commit -m "Document FastAPI p115 runtime" -m "Update project documentation to match the new PanSou, p115, AList, and built-in STRM workflow after CloudSaver is removed from runtime use." -m "Constraint: Keep historical design and plan docs intact for migration traceability." -m "Tested: PYTHONPATH=. pytest -v; npm run build" -m "Co-authored-by: OmX <omx@oh-my-codex.dev>"
```

## Final Manual Validation On Server

- [ ] Copy `backend_py/.env.example` to `backend_py/.env` and set `P115_COOKIE`, `ALIST_URL`, `STRM_SERVER`, and `STRM_SAVE_DIR`.
- [ ] On server `192.168.70.197`, run `docker compose up -d --build`.
- [ ] Open frontend at the configured host and search a known title.
- [ ] Start one transfer task from a PanSou 115 result.
- [ ] Confirm task logs show p115 transfer success, AList refresh/list, and STRM generation.
- [ ] Confirm generated STRM files exist under the mounted STRM directory.
- [ ] Confirm Emby can play one generated STRM through AList 302.

## Self-Review

- Spec coverage: This plan covers FastAPI backend creation, API compatibility, PanSou-only search, p115 transfer validation and adapter, AList refresh, built-in STRM generation, task workflow, SSE logs, Docker deployment, and CloudSaver runtime cleanup.
- Placeholder scan: The plan contains no unfinished markers or vague implementation steps.
- Type consistency: Resource fields use the existing camelCase frontend contract (`mediaType`, `shareUrl`, `transferStatus`, `strmStatus`) while Python internals keep explicit model names.
