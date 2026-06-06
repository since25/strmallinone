import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend_py.app.adapters.p115_adapter import P115TransferAdapter
from backend_py.app.models.resource import ResourceDto


class FakeClient:
    def __init__(self, cookie: str):
        self.cookie = cookie
        self.received_payload = None

    def fs_files(self, payload):
        return {"state": True, "data": [{"name": "automv", "cid": "100", "is_dir": True}]}

    def share_snap(self, payload):
        return {"state": True, "data": {"list": [{"file_id": "200", "file_name": "Movie Folder", "is_dir": True}]}}

    def share_receive(self, payload):
        self.received_payload = payload
        return {"state": True, "message": "ok"}


class FakeMissingFolderClient(FakeClient):
    def __init__(self, cookie: str):
        super().__init__(cookie)
        self.created_folder = None

    def fs_files(self, payload):
        if self.created_folder:
            return {"state": True, "data": [{"name": self.created_folder, "cid": "101", "is_dir": True}]}
        return {"state": True, "data": []}

    def fs_mkdir(self, payload, pid=0):
        self.created_folder = payload
        return {"state": True, "data": {"cid": "101"}}


class FakeDuplicateFolderClient(FakeMissingFolderClient):
    def fs_mkdir(self, payload, pid=0):
        self.created_folder = payload
        return {"state": False, "message": "该目录名称已存在。"}

    def fs_dir_getid(self, payload):
        return {"state": True, "data": "102"}


def test_transfer_receives_share_into_movie_folder():
    resource = ResourceDto(
        id="pansou_sabc_ABCD",
        title="Movie Folder",
        provider="115",
        mediaType="movie",
        rawType="video",
        size="-",
        shareUrl="https://115cdn.com/s/sabc?password=ABCD",
        extra={"shareCode": "sabc", "receiveCode": "ABCD"},
    )
    client = FakeClient("cookie")
    adapter = P115TransferAdapter(
        cookie="cookie",
        default_movie_folder="automv",
        default_tv_folder="autotv",
        alist_base_path="/115",
        client_factory=lambda cookie: client,
    )

    result = adapter.transfer(resource)

    assert result.success is True
    assert result.data is not None
    assert result.data.savePath == "/115/automv/Movie Folder"
    assert client.received_payload == {
        "share_code": "sabc",
        "receive_code": "ABCD",
        "file_id": "200",
        "cid": "100",
        "is_check": 0,
    }


def test_transfer_creates_missing_target_folder():
    resource = ResourceDto(
        id="pansou_sabc_ABCD",
        title="Movie Folder",
        provider="115",
        mediaType="movie",
        rawType="video",
        size="-",
        shareUrl="https://115cdn.com/s/sabc?password=ABCD",
        extra={"shareCode": "sabc", "receiveCode": "ABCD"},
    )
    client = FakeMissingFolderClient("cookie")
    adapter = P115TransferAdapter(
        cookie="cookie",
        default_movie_folder="automv",
        default_tv_folder="autotv",
        alist_base_path="/115",
        client_factory=lambda cookie: client,
    )

    result = adapter.transfer(resource)

    assert result.success is True
    assert client.created_folder == "automv"
    assert client.received_payload["cid"] == "101"


def test_transfer_uses_existing_folder_when_create_reports_duplicate():
    resource = ResourceDto(
        id="pansou_sabc_ABCD",
        title="Movie Folder",
        provider="115",
        mediaType="movie",
        rawType="video",
        size="-",
        shareUrl="https://115cdn.com/s/sabc?password=ABCD",
        extra={"shareCode": "sabc", "receiveCode": "ABCD"},
    )
    client = FakeDuplicateFolderClient("cookie")
    adapter = P115TransferAdapter(
        cookie="cookie",
        default_movie_folder="automv",
        default_tv_folder="autotv",
        alist_base_path="/115",
        client_factory=lambda cookie: client,
    )

    result = adapter.transfer(resource)

    assert result.success is True
    assert client.created_folder == "automv"
    assert client.received_payload["cid"] == "102"


def test_transfer_reports_missing_share_params():
    resource = ResourceDto(
        id="bad",
        title="Bad",
        provider="115",
        mediaType="movie",
        rawType="video",
        size="-",
        shareUrl="",
        extra={},
    )
    adapter = P115TransferAdapter("cookie", "automv", "autotv", "/115", client_factory=FakeClient)

    result = adapter.transfer(resource)

    assert result.success is False
    assert result.message == "资源缺少 115 shareCode 或 receiveCode"
