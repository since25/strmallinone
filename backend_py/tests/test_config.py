import importlib
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent


def test_settings_paths_are_anchored_to_backend_dir():
    sys.path.insert(0, str(REPO_ROOT))
    config = importlib.import_module("backend_py.app.config")

    assert config.Settings.model_config["env_file"] == (REPO_ROOT / ".env", BACKEND_DIR / ".env")
    assert config.Settings.model_fields["database_path"].default == BACKEND_DIR / "data" / "app.db"
