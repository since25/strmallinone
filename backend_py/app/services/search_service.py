from ..adapters.pansou import PanSouClient
from ..models.resource import MediaType, ResourceDto
from ..repositories.search_history_repository import SearchHistoryRepository
from .resource_identity import dedupe_resources


class SearchService:
    def __init__(self, pansou: PanSouClient, history: SearchHistoryRepository):
        self.pansou = pansou
        self.history = history

    async def search(self, keyword: str, driver: str, media_type: MediaType) -> list[ResourceDto]:
        resources = dedupe_resources(await self.pansou.search(keyword, media_type))
        self.history.create(keyword=keyword, driver=driver, result_count=len(resources))
        return resources
