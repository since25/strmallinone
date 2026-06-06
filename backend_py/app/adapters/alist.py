from urllib.parse import quote

import httpx


class AListClient:
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": token} if token else {}

    def list_dir(self, path: str, refresh: bool = False) -> list[dict] | None:
        response = httpx.post(
            f"{self.base_url}/api/fs/list",
            headers=self.headers,
            json={"path": path, "refresh": refresh, "password": "", "page": 1, "per_page": 0},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != 200:
            return None
        return payload.get("data", {}).get("content") or []

    def file_exists(self, path: str) -> bool:
        response = httpx.post(
            f"{self.base_url}/api/fs/get",
            headers=self.headers,
            json={"path": path, "password": ""},
            timeout=15,
        )
        response.raise_for_status()
        return response.json().get("code") == 200

    def mkdir(self, path: str) -> bool:
        response = httpx.post(
            f"{self.base_url}/api/fs/mkdir",
            headers=self.headers,
            json={"path": path},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("code") == 200

    def ensure_dir(self, path: str) -> None:
        segments = path.strip("/").split("/")
        current = ""
        for seg in segments:
            current = f"{current}/{seg}"
            self.mkdir(current)

    def upload_file(self, remote_path: str, content: bytes) -> bool:
        parent = "/" + "/".join(remote_path.strip("/").split("/")[:-1])
        if parent and parent != "/":
            self.ensure_dir(parent)
        encoded_path = quote(remote_path, safe="/")
        headers = {
            **self.headers,
            "file-path": encoded_path,
            "Content-Type": "application/octet-stream",
            "As-Task": "false",
        }
        response = httpx.put(
            f"{self.base_url}/api/fs/put",
            headers=headers,
            content=content,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("code") == 200
