from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import health, search
from .adapters.pansou import PanSouClient
from .config import get_settings
from .repositories.database import Database
from .repositories.search_history_repository import SearchHistoryRepository
from .services.search_service import SearchService


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
