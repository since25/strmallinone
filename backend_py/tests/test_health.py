import importlib
import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent


def import_create_app(module_name: str):
    return importlib.import_module(module_name).create_app


def test_health_returns_ok():
    sys.path.insert(0, str(BACKEND_DIR))
    create_app = import_create_app("app.main")
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"status": "ok"}}


def test_repo_root_package_import_returns_ok():
    sys.path.insert(0, str(REPO_ROOT))
    create_app = import_create_app("backend_py.app.main")
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"status": "ok"}}


def test_repo_root_import_works_without_backend_dir_on_path():
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from backend_py.app.main import create_app; "
                "from fastapi.testclient import TestClient; "
                "response = TestClient(create_app()).get('/api/health'); "
                "assert response.json() == {'success': True, 'data': {'status': 'ok'}}"
            ),
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
