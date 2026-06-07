import re

import httpx

from ..models.resource import MediaType, ResourceDto

LINK_RE = re.compile(r"(?P<url>https?://[^\s，。；;]+/s/(?P<share>[a-z0-9]+)(?:\?password=(?P<pwd>[A-Za-z0-9]{4}))?)", re.I)
CODE_RE = re.compile(r"(?:提取码|访问码|密码)\s*[:：]?\s*(?P<code>[A-Za-z0-9]{4})", re.I)


def parse_115_share_text(text: str, password: str | None = None) -> tuple[str, str, str] | None:
    match = LINK_RE.search(text.strip())
    if not match:
        return None
    receive_code = password or match.group("pwd")
    if not receive_code:
        code_match = CODE_RE.search(text)
        receive_code = code_match.group("code") if code_match else None
    if not receive_code:
        return None
    return match.group("url"), match.group("share"), receive_code


def parse_115_link(url: str, password: str | None = None) -> tuple[str, str] | None:
    parsed = parse_115_share_text(url, password)
    if not parsed:
        return None
    _, share_code, receive_code = parsed
    return share_code, receive_code


def map_pansou_item(item: dict[str, object], media_type: MediaType) -> ResourceDto | None:
    url = str(item.get("url") or "")
    if "115" not in url:
        return None
    parsed = parse_115_link(url, str(item.get("password") or "") or None)
    if not parsed:
        return None
    share_code, receive_code = parsed
    title = str(item.get("name") or item.get("title") or item.get("note") or share_code)
    return ResourceDto(
        id=f"pansou_{share_code}_{receive_code}",
        title=title,
        provider="115",
        mediaType=media_type,
        rawType="video",
        size=str(item.get("size") or "-"),
        shareUrl=url,
        extra={
            "source": "pansou",
            "shareCode": share_code,
            "receiveCode": receive_code,
            "raw": item,
        },
    )


class PanSouClient:
    def __init__(
        self,
        base_url: str,
        search_path: str,
        transport: httpx.AsyncBaseTransport | httpx.BaseTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.search_path = search_path
        self.transport = transport

    async def search(self, keyword: str, media_type: MediaType) -> list[ResourceDto]:
        async with httpx.AsyncClient(base_url=self.base_url, transport=self.transport, timeout=30) as client:
            response = await client.post(self.search_path, json={"kw": keyword, "cloud_types": ["115"]})
            response.raise_for_status()
            payload = response.json()
        items = payload.get("data", {}).get("merged_by_type", {}).get("115", [])
        return [
            resource
            for item in items
            if isinstance(item, dict)
            for resource in [map_pansou_item(item, media_type)]
            if resource is not None
        ]
