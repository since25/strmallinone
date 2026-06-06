from collections.abc import Callable
from uuid import uuid4

from p115client import P115Client

from ..models.resource import ResourceDto
from ..models.transfer import TransferData, TransferResult


def ok_response(resp: dict) -> bool:
    message = str(resp.get("message") or resp.get("error") or "")
    return bool(
        resp.get("state") is True
        or resp.get("code") in {0, 200}
        or resp.get("errno") == 0
        or "已接收" in message
        or "无需重复" in message
    )


def item_name(item: dict) -> str:
    return str(item.get("file_name") or item.get("name") or item.get("n") or "")


def item_id(item: dict) -> str:
    value = item.get("file_id") or item.get("fid") or item.get("cid")
    return str(value or "")


def folder_id_from_response(resp: dict) -> str:
    top_level_value = resp.get("file_id") or resp.get("fid") or resp.get("cid") or resp.get("id")
    if top_level_value:
        return str(top_level_value)
    data = resp.get("data") or {}
    if isinstance(data, dict):
        value = data.get("file_id") or data.get("fid") or data.get("cid") or data.get("id")
        return str(value or "")
    if isinstance(data, str | int):
        return str(data)
    return ""


def item_is_dir(item: dict) -> bool:
    return bool(item.get("is_dir") or item.get("fc") == "0" or item.get("ico") == "folder")


class P115TransferAdapter:
    def __init__(
        self,
        cookie: str,
        default_movie_folder: str,
        default_tv_folder: str,
        alist_base_path: str,
        client_factory: Callable[[str], object] = P115Client,
    ):
        self.cookie = cookie
        self.default_movie_folder = default_movie_folder
        self.default_tv_folder = default_tv_folder
        self.alist_base_path = alist_base_path.rstrip("/")
        self.client = client_factory(cookie)

    def target_folder_name(self, resource: ResourceDto) -> str:
        return self.default_tv_folder if resource.mediaType == "tv" else self.default_movie_folder

    def find_target_folder(self, folder_name: str) -> str:
        resp = self.client.fs_files({"cid": 0, "limit": 1150, "offset": 0, "show_dir": 1})
        children = resp.get("data", [])
        if isinstance(children, dict):
            children = children.get("data") or children.get("list") or []
        for item in children:
            if item_name(item) == folder_name and item_is_dir(item):
                folder_id = item_id(item)
                if folder_id:
                    return folder_id
        raise RuntimeError(f"未找到目标目录: {folder_name}")

    def create_target_folder(self, folder_name: str) -> str:
        resp = self.client.fs_mkdir(folder_name, pid=0)
        if not ok_response(resp):
            message = str(resp.get("message") or resp.get("error") or "")
            if "目录名称已存在" in message or "已存在" in message:
                return self.find_target_folder_by_path(folder_name)
            raise RuntimeError(str(resp.get("message") or resp.get("error") or f"创建目标目录失败: {folder_name}"))
        folder_id = folder_id_from_response(resp)
        if folder_id:
            return folder_id
        return self.find_target_folder(folder_name)

    def find_target_folder_by_path(self, folder_name: str) -> str:
        resp = self.client.fs_dir_getid(f"/{folder_name.strip('/')}")
        if not ok_response(resp):
            raise RuntimeError(str(resp.get("message") or resp.get("error") or f"获取目标目录失败: {folder_name}"))
        folder_id = folder_id_from_response(resp)
        if not folder_id:
            raise RuntimeError(f"目标目录缺少 cid: {folder_name}")
        return folder_id

    def ensure_target_folder(self, folder_name: str) -> str:
        try:
            return self.find_target_folder(folder_name)
        except RuntimeError as exc:
            if str(exc) != f"未找到目标目录: {folder_name}":
                raise
            return self.create_target_folder(folder_name)

    def first_share_file(self, share_code: str, receive_code: str) -> dict:
        resp = self.client.share_snap({"share_code": share_code, "receive_code": receive_code, "cid": 0, "limit": 32})
        if not ok_response(resp):
            raise RuntimeError(str(resp.get("message") or resp.get("error") or "读取 115 分享失败"))
        data = resp.get("data") or {}
        items = data.get("list") or data.get("data") or []
        if not items:
            raise RuntimeError("分享链接为空，未获取到可转存文件")
        return items[0]

    def transfer(self, resource: ResourceDto) -> TransferResult:
        share_code = str(resource.extra.get("shareCode") or "")
        receive_code = str(resource.extra.get("receiveCode") or "")
        if not share_code or not receive_code:
            return TransferResult(success=False, message="资源缺少 115 shareCode 或 receiveCode")

        folder_name = self.target_folder_name(resource)
        target_cid = self.ensure_target_folder(folder_name)
        primary = self.first_share_file(share_code, receive_code)
        file_id = item_id(primary)
        source_name = item_name(primary) or resource.title
        if not file_id:
            return TransferResult(success=False, message="分享文件缺少 file_id", raw={"shareFile": primary})

        receive_resp = self.client.share_receive(
            {
                "share_code": share_code,
                "receive_code": receive_code,
                "file_id": file_id,
                "cid": target_cid,
                "is_check": 0,
            }
        )
        message = str(receive_resp.get("message") or receive_resp.get("error") or "")
        duplicate = "已接收" in message or "无需重复" in message
        if not ok_response(receive_resp):
            return TransferResult(success=False, message=message or "115 转存失败", raw=receive_resp)

        return TransferResult(
            success=True,
            message="115 文件已存在，跳过重复接收" if duplicate else "115 转存成功",
            data=TransferData(
                savePath=f"{self.alist_base_path}/{folder_name}/{source_name}",
                sourceName=source_name,
                savedName=source_name,
                fileCount=1,
                transferId=uuid4().hex,
                duplicate=duplicate,
            ),
            raw={"receiveResponse": receive_resp, "shareFile": primary},
        )
