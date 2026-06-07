import sys
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend_py.app.main import create_app
from backend_py.app.models.resource import ResourceDto


def test_create_transfer_task_returns_task_id():
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


def test_create_manual_transfer_task_parses_share_text_and_returns_task_id():
    app = create_app()
    seen = {}

    async def fake_run(task_id, resource):
        seen["task_id"] = task_id
        seen["resource"] = resource
        app.state.task_log_service.append(task_id, "success", "fake manual workflow done")

    app.state.workflow_service.run = fake_run
    client = TestClient(app)

    response = client.post(
        "/api/tasks/manual-transfer",
        json={"shareText": "资源：https://115.com/s/sabc123\n提取码：t58d", "mediaType": "tv"},
    )

    assert response.status_code == 201
    task_id = response.json()["data"]["taskId"]
    task_response = client.get(f"/api/tasks/{task_id}")
    data = task_response.json()["data"]
    assert data["keyword"] == "手动 115 转存"
    assert data["resourceTitle"] == "手动 115 转存 sabc123"
    assert seen["resource"].mediaType == "tv"
    assert seen["resource"].shareUrl == "https://115.com/s/sabc123"
    assert seen["resource"].extra["source"] == "manual"
    assert seen["resource"].extra["shareCode"] == "sabc123"
    assert seen["resource"].extra["receiveCode"] == "t58d"


def test_create_manual_transfer_task_rejects_invalid_share_text():
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/tasks/manual-transfer",
        json={"shareText": "只有链接 https://115.com/s/sabc123", "mediaType": "movie"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "未找到有效的 115 分享链接或提取码"


def test_create_manual_transfer_task_rejects_non_115_host():
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/tasks/manual-transfer",
        json={"shareText": "https://anxia.com/s/sabc123 提取码 t58d", "mediaType": "movie"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "未找到有效的 115 分享链接或提取码"


def test_task_logs_endpoint_returns_existing_logs():
    app = create_app()
    client = TestClient(app)
    task_id = f"task_existing_{uuid4().hex[:8]}"
    resource = {
        "id": "pansou_sabc_ABCD",
        "title": "Movie",
        "provider": "115",
        "mediaType": "movie",
        "rawType": "video",
        "size": "-",
        "shareUrl": "https://115cdn.com/s/sabc?password=ABCD",
        "extra": {"shareCode": "sabc", "receiveCode": "ABCD"},
    }
    app.state.task_repository.create(task_id, "movie", ResourceDto(**resource))
    app.state.task_log_service.append(task_id, "info", "hello")

    response = client.get(f"/api/tasks/{task_id}/logs")

    assert response.status_code == 200
    assert response.json()["data"][0]["message"] == "hello"
