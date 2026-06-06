import json
import os
import re
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from p115client import P115Client


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def parse_share_input(raw_share: str, raw_receive: str) -> tuple[str, str]:
    if raw_share.startswith(("http://", "https://")):
        parsed = urlparse(raw_share)
        match = re.search(r"/s/([^/?#]+)", parsed.path)
        if not match:
            raise SystemExit("P115_SHARE_CODE contains a URL but no /s/<share_code> segment")
        query = parse_qs(parsed.query)
        receive_code = (query.get("password") or query.get("pwd") or [""])[0] or raw_receive
        if not receive_code:
            raise SystemExit("Missing receive code; set P115_RECEIVE_CODE or include password= in the share URL")
        return match.group(1), receive_code

    if "-" in raw_share and not raw_receive:
        share_code, receive_code = raw_share.split("-", 1)
        return share_code, receive_code

    return raw_share, raw_receive


def response_ok(resp: dict) -> bool:
    message = str(resp.get("message") or "")
    return bool(
        resp.get("state") is True
        or resp.get("code") in {0, 200}
        or resp.get("errno") in {0, None}
        or "已接收" in message
        or "无需重复" in message
    )


def list_children(client: P115Client, cid: int | str) -> list[dict]:
    resp = client.fs_files({"cid": cid, "limit": 1150, "offset": 0, "show_dir": 1})
    data = resp.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data") or data.get("list") or []
    return []


def item_name(item: dict) -> str:
    return str(item.get("n") or item.get("name") or item.get("file_name") or "")


def item_id(item: dict) -> str:
    value = item.get("fid") or item.get("cid") or item.get("file_id")
    return str(value or "")


def item_is_dir(item: dict) -> bool:
    return bool(item.get("is_dir") or item.get("fc") == "0" or item.get("ico") == "folder")


def ensure_folder(client: P115Client, parent_id: int, folder_name: str) -> int:
    for item in list_children(client, parent_id):
        if item_name(item) == folder_name and item_id(item) and item_is_dir(item):
            return int(item_id(item))
    resp = client.fs_mkdir(folder_name, pid=parent_id)
    if not response_ok(resp):
        raise RuntimeError(f"fs_mkdir failed: {resp}")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    folder_id = resp.get("id") or resp.get("cid") or resp.get("file_id") or data.get("file_id") or data.get("cid")
    if not folder_id:
        raise RuntimeError(f"fs_mkdir returned no folder id: {resp}")
    return int(folder_id)


def first_share_file(client: P115Client, share_code: str, receive_code: str) -> dict:
    resp = client.share_snap({"share_code": share_code, "receive_code": receive_code, "cid": 0, "limit": 32})
    if not response_ok(resp):
        raise RuntimeError(f"share_snap failed: {resp}")
    data = resp.get("data") or {}
    items = data.get("list") or data.get("data") or []
    if not items:
        raise RuntimeError(f"share contains no files: {resp}")
    return items[0]


def main() -> int:
    cookie = require_env("P115_COOKIE")
    raw_share = require_env("P115_SHARE_CODE")
    raw_receive = os.environ.get("P115_RECEIVE_CODE", "").strip()
    share_code, receive_code = parse_share_input(raw_share, raw_receive)
    if not receive_code:
        raise SystemExit("Missing required environment variable: P115_RECEIVE_CODE")
    target_parent_id = int(os.environ.get("P115_TARGET_PARENT_ID", "0"))
    target_folder_name = os.environ.get("P115_PROBE_FOLDER", f"strmallinone_probe_{uuid4().hex[:8]}")

    client = P115Client(cookie)
    target_cid = ensure_folder(client, target_parent_id, target_folder_name)
    share_file = first_share_file(client, share_code, receive_code)
    file_id = item_id(share_file)
    file_name = item_name(share_file) or str(file_id)
    if not file_id:
        raise RuntimeError(f"share file has no id: {share_file}")

    receive_resp = client.share_receive(
        {
            "share_code": share_code,
            "receive_code": receive_code,
            "file_id": file_id,
            "cid": str(target_cid),
            "is_check": 0,
        }
    )
    if not response_ok(receive_resp):
        raise RuntimeError(f"share_receive failed: {receive_resp}")

    print(
        json.dumps(
            {
                "success": True,
                "targetCid": target_cid,
                "targetFolder": target_folder_name,
                "fileId": file_id,
                "fileName": file_name,
                "receiveState": receive_resp.get("state"),
                "receiveCode": receive_resp.get("code"),
                "receiveMessage": receive_resp.get("message"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
