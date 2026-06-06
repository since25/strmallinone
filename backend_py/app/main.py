from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import health, search, strm_compat, tasks
from .adapters.alist import AListClient
from .adapters.p115_adapter import P115TransferAdapter
from .adapters.pansou import PanSouClient
from .config import get_settings
from .repositories.database import Database
from .repositories.search_history_repository import SearchHistoryRepository
from .repositories.task_log_repository import TaskLogRepository
from .repositories.task_repository import TaskRepository
from .services.search_service import SearchService
from .services.strm_service import StrmConfig, StrmService
from .services.task_log_service import TaskLogService
from .services.workflow_service import WorkflowService


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

    alist_client = AListClient(settings.alist_url, settings.alist_token)

    strm_service = StrmService(
        alist_client,
        StrmConfig(
            strm_server=settings.normalized_strm_server(),
            strm_save_dir=settings.strm_save_dir,
            strm_alist_base_path=settings.strm_alist_base_path,
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
    app.include_router(strm_compat.router)
    return app


app = create_app()
