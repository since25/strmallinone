from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ..models.resource import MediaType

router = APIRouter()


class SearchRequest(BaseModel):
    keyword: str = Field(min_length=1)
    driver: Literal["115"] = "115"
    mediaType: MediaType = "movie"


@router.post("/search")
async def search(payload: SearchRequest, request: Request):
    data = await request.app.state.search_service.search(payload.keyword.strip(), payload.driver, payload.mediaType)
    return {"success": True, "data": [item.model_dump() for item in data]}
