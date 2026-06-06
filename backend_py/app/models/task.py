from typing import Literal

from pydantic import BaseModel

from .resource import ResourceDto

StepStatus = Literal["pending", "success", "failed"]
TaskStatus = Literal["pending", "running", "success", "failed"]
LogLevel = Literal["info", "success", "error"]


class TaskDto(BaseModel):
    id: str
    keyword: str
    provider: str
    resourceTitle: str
    resource: ResourceDto
    status: TaskStatus
    transferStatus: StepStatus
    strmStatus: StepStatus
    errorMessage: str | None
    createdAt: str
    updatedAt: str


class TaskLogDto(BaseModel):
    id: int
    taskId: str
    level: LogLevel
    message: str
    createdAt: str
