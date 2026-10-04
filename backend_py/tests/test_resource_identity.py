from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend_py.app.models.resource import ResourceDto
from backend_py.app.services.resource_identity import dedupe_resources, resource_key, target_folder


def resource(title: str, receive: str = "ABCD", source: str = "pansou") -> ResourceDto:
    return ResourceDto(
        id=f"{title}-{receive}", title=title, provider="115", mediaType="movie", rawType="video", size="-",
        shareUrl=f"https://115.com/s/share?password={receive}",
        extra={"shareCode": "share", "receiveCode": receive, "source": source},
    )


def test_resource_key_ignores_title_and_id():
    assert resource_key(resource("first")) == resource_key(resource("second"))


def test_dedupe_keeps_first_and_aggregates_sources():
    result = dedupe_resources([resource("first", source="pansou"), resource("second", source="manual")])
    assert len(result) == 1
    assert result[0].title == "first"
    assert result[0].extra["sources"] == ["pansou", "manual"]


def test_receive_code_and_media_type_change_identity_or_folder():
    assert resource_key(resource("first", "ABCD")) != resource_key(resource("first", "EFGH"))
    tv = resource("show").model_copy(update={"mediaType": "tv"})
    assert target_folder(tv, "automv", "autotv") == "autotv"
