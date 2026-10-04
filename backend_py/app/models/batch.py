from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .resource import ResourceDto

BatchStatus = Literal["pending", "running", "success", "partial", "failed"]
BatchItemStatus = Literal["pending", "running", "success", "skipped", "failed"]


class BatchDto(BaseModel):
    id: str
    keyword: str
    status: BatchStatus
    concurrency: int
    totalCount: int
    pendingCount: int
    runningCount: int
    successCount: int
    skippedCount: int
    failedCount: int
    errorMessage: str | None = None
    createdAt: str
    updatedAt: str


class BatchItemDto(BaseModel):
    id: str
    batchId: str
    taskId: str | None = None
    resourceKey: str
    resource: ResourceDto
    status: BatchItemStatus
    duplicate: bool = False
    reused: bool = False
    errorMessage: str | None = None
    retryCount: int = 0
    createdAt: str
    updatedAt: str


class CreateBatchRequest(BaseModel):
    keyword: str = ""
    items: list[ResourceDto] = Field(min_length=1)
    concurrency: int = Field(default=2)

    @field_validator("concurrency", mode="before")
    @classmethod
    def clamp_concurrency(cls, value: object) -> int:
        try:
            return max(1, min(4, int(value)))
        except (TypeError, ValueError) as exc:
            raise ValueError("concurrency must be an integer") from exc
