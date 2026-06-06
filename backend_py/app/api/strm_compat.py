from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class StrmPathRequest(BaseModel):
    path: str | None = None
    full_path: str | None = None
    folder_name: str | None = None
    savepath: str | None = None


class StrmDirectRequest(BaseModel):
    files: list[str]


def summarize(message: str, path: str | None, result: dict[str, list[str]]) -> dict:
    return {
        "code": 200,
        "message": message,
        "path": path,
        "created_count": len(result["created"]),
        "skipped_count": len(result["skipped"]),
        "error_count": len(result["errors"]),
        "details": result,
    }


@router.post("/webhook/strm")
def webhook_strm(payload: StrmPathRequest, request: Request):
    path = payload.path or payload.full_path or payload.folder_name or payload.savepath
    if not path:
        raise HTTPException(status_code=400, detail="缺少 path 参数")
    if not path.startswith("/"):
        path = f"/{path}"
    result = request.app.state.strm_service.generate_for_path(path)
    return summarize("STRM 生成完成", path, result)


@router.post("/webhook/strm/direct")
def webhook_strm_direct(payload: StrmDirectRequest, request: Request):
    if not payload.files:
        raise HTTPException(status_code=400, detail="缺少 files 参数")
    result = request.app.state.strm_service.generate_direct(payload.files)
    return summarize("STRM 直传生成完成", None, result)
