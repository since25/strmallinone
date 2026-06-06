from typing import Literal

from pydantic import BaseModel, Field

Provider = Literal["115"]
MediaType = Literal["movie", "tv"]


class ResourceDto(BaseModel):
    id: str
    title: str
    provider: Provider
    mediaType: MediaType
    rawType: str
    size: str
    shareUrl: str
    extra: dict[str, object] = Field(default_factory=dict)
