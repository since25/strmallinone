from pydantic import BaseModel, Field


class TransferData(BaseModel):
    savePath: str
    sourceName: str
    savedName: str
    fileCount: int
    transferId: str
    duplicate: bool = False


class TransferResult(BaseModel):
    success: bool
    message: str
    data: TransferData | None = None
    raw: dict[str, object] = Field(default_factory=dict)
