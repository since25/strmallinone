import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend_py.app.main import create_app


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
