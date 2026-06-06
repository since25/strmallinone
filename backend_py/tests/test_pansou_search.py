import json
import sys
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend_py.app.adapters.pansou import PanSouClient, map_pansou_item
from backend_py.app.main import create_app
from backend_py.app.repositories.database import Database
from backend_py.app.repositories.search_history_repository import SearchHistoryRepository
from backend_py.app.services.search_service import SearchService


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


def test_map_pansou_item_uses_note_title():
    item = {
        "url": "https://115cdn.com/s/swwm6qp3zrk?password=t58d",
        "password": "t58d",
        "note": "Movie note title",
    }

    resource = map_pansou_item(item, "movie")

    assert resource is not None
    assert resource.title == "Movie note title"


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


def test_search_api_keeps_response_shape():
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
