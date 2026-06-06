from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"), extra="ignore")

    port: int = Field(default=3000, alias="PORT")
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")
    database_path: Path = Field(default=BACKEND_DIR / "data" / "app.db", alias="DATABASE_PATH")

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
    strm_alist_base_path: str = Field(default="", alias="STRM_ALIST_BASE_PATH")
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
