from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import quote

MediaType = Literal["movie", "tv"]


@dataclass(frozen=True)
class StrmConfig:
    strm_server: str
    strm_save_dir: Path
    strm_replace_path: str
    video_exts: set[str]
    movie_folder: str = "automv"
    tv_folder: str = "autotv"


class StrmService:
    def __init__(self, alist, config: StrmConfig):
        self.alist = alist
        self.config = config

    def generate_for_path(self, alist_path: str, media_type: MediaType | None = None) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {"created": [], "skipped": [], "errors": []}
        if self.is_video_path(alist_path):
            self.process_file(alist_path if alist_path.startswith("/") else f"/{alist_path}", result, media_type)
            return result
        actual_path = self.resolve_actual_path(alist_path)
        if not actual_path:
            result["errors"].append(f"解析路径失败: {alist_path}")
            return result
        items = self.alist.list_dir(actual_path, refresh=True)
        if items is None:
            result["errors"].append(f"无法列出目录: {actual_path}")
            return result
        self.process_items(actual_path, items, result, media_type)
        return result

    def generate_direct(self, files: list[str]) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {"created": [], "skipped": [], "errors": []}
        for file_path in files:
            self.process_file(file_path if file_path.startswith("/") else f"/{file_path}", result)
        return result

    def resolve_actual_path(self, target_path: str) -> str | None:
        segments = target_path.strip("/").split("/") if target_path.strip("/") else []
        current = ""
        index = 0
        while index < len(segments):
            parent = current or "/"
            items = self.alist.list_dir(parent, refresh=True)
            if items is None:
                return None
            matched = None
            consumed = 0
            for count in range(len(segments) - index, 0, -1):
                candidate = "/".join(segments[index : index + count])
                matched = self.find_item(candidate, items)
                if matched:
                    consumed = count
                    break
            if not matched:
                return None
            current = f"{current}/{matched}".replace("//", "/")
            index += consumed
        return current or "/"

    def find_item(self, target_name: str, items: list[dict]) -> str | None:
        def normalize(value: str) -> str:
            normalized = value.strip().lower()
            for char in ["/", "|", "／", "\\", " "]:
                normalized = normalized.replace(char, "")
            return normalized

        for item in items:
            name = str(item.get("name", ""))
            if name == target_name:
                return name
        target = normalize(target_name)
        for item in items:
            name = str(item.get("name", ""))
            if normalize(name) == target:
                return name
        return None

    def process_items(
        self, dir_path: str, items: list[dict], result: dict[str, list[str]], media_type: MediaType | None = None
    ) -> None:
        for item in items:
            name = str(item.get("name", ""))
            item_path = f"{dir_path}/{name}".replace("//", "/")
            if item.get("is_dir"):
                child_items = self.alist.list_dir(item_path, refresh=False)
                if child_items is None:
                    result["errors"].append(f"无法列出目录: {item_path}")
                    continue
                self.process_items(item_path, child_items, result, media_type)
            else:
                self.process_file(item_path, result, media_type)

    def process_file(self, file_path: str, result: dict[str, list[str]], media_type: MediaType | None = None) -> None:
        if not self.is_video_path(file_path):
            return
        strm_path = self.strm_output_path(file_path, media_type)
        full_path = self.config.strm_save_dir / str(strm_path).lstrip("/")
        if full_path.exists():
            result["skipped"].append(str(full_path))
            return
        full_path.parent.mkdir(parents=True, exist_ok=True)
        strm_file_path = file_path
        if self.config.strm_replace_path:
            parts = file_path.split("/", 2)
            if len(parts) >= 3:
                strm_file_path = f"{self.config.strm_replace_path}/{parts[2]}"
        content = f"{self.config.strm_server.rstrip('/')}{quote(strm_file_path, safe='/')}"
        full_path.write_text(content, encoding="utf-8")
        result["created"].append(str(full_path))

    def is_video_path(self, file_path: str) -> bool:
        ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
        return ext in self.config.video_exts

    def strm_output_path(self, file_path: str, media_type: MediaType | None = None) -> Path:
        if media_type is None:
            return Path(file_path).with_suffix(".strm")

        target_folder = self.config.tv_folder if media_type == "tv" else self.config.movie_folder
        segments = Path(file_path).with_suffix(".strm").parts
        if len(segments) >= 4 and segments[0] == "/" and segments[1] == "115" and segments[2] in {
            self.config.movie_folder,
            self.config.tv_folder,
        }:
            return Path(target_folder, *segments[3:])
        return Path(target_folder, *Path(file_path).with_suffix(".strm").parts[1:])
