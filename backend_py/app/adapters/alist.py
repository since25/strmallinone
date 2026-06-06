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
