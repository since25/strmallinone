import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend_py.app.services.strm_service import StrmConfig, StrmService


class FakeAList:
    def __init__(self):
        self.tree = {
            "/": [{"name": "115", "is_dir": True}],
            "/115": [{"name": "automv", "is_dir": True}],
            "/115/automv": [{"name": "Movie Folder", "is_dir": True}],
            "/115/automv/Movie Folder": [
                {"name": "Movie.mkv", "is_dir": False},
                {"name": "poster.jpg", "is_dir": False},
            ],
        }

    def list_dir(self, path: str, refresh: bool = False):
        return self.tree.get(path)


def test_generate_for_path_writes_video_strm(tmp_path: Path):
    service = StrmService(
        FakeAList(),
        StrmConfig(
            strm_server="http://alist.local/d",
            strm_save_dir=tmp_path,
            strm_replace_path="",
            video_exts={"mkv"},
        ),
    )

    result = service.generate_for_path("/115/automv/Movie Folder")

    output = tmp_path / "115" / "automv" / "Movie Folder" / "Movie.strm"
    assert output.read_text() == "http://alist.local/d/115/automv/Movie%20Folder/Movie.mkv"
    assert result["created"] == [str(output)]
    assert result["skipped"] == []
    assert result["errors"] == []


def test_generate_for_path_writes_single_video_file(tmp_path: Path):
    service = StrmService(
        FakeAList(),
        StrmConfig("http://alist.local/d", tmp_path, "", {"mkv"}),
    )

    result = service.generate_for_path("/115/automv/Movie.mkv")

    output = tmp_path / "115" / "automv" / "Movie.strm"
    assert result["created"] == [str(output)]
    assert result["errors"] == []
    assert output.read_text() == "http://alist.local/d/115/automv/Movie.mkv"


def test_generate_for_movie_writes_to_movie_strm_folder(tmp_path: Path):
    service = StrmService(
        FakeAList(),
        StrmConfig(
            strm_server="http://alist.local/d",
            strm_save_dir=tmp_path,
            strm_replace_path="",
            video_exts={"mkv"},
            movie_folder="automv",
            tv_folder="autotv",
        ),
    )

    result = service.generate_for_path("/115/automv/Movie.mkv", media_type="movie")

    output = tmp_path / "automv" / "Movie.strm"
    assert result["created"] == [str(output)]
    assert output.read_text() == "http://alist.local/d/115/automv/Movie.mkv"


def test_direct_files_skip_existing(tmp_path: Path):
    output = tmp_path / "115" / "automv" / "Movie.strm"
    output.parent.mkdir(parents=True)
    output.write_text("old")
    service = StrmService(
        FakeAList(),
        StrmConfig("http://alist.local/d", tmp_path, "", {"mkv"}),
    )

    result = service.generate_direct(["/115/automv/Movie.mkv"])

    assert result["created"] == []
    assert result["skipped"] == [str(output)]
    assert output.read_text() == "old"


def test_path_replacement_changes_strm_content(tmp_path: Path):
    service = StrmService(
        FakeAList(),
        StrmConfig("http://alist.local/d", tmp_path, "/media115", {"mkv"}),
    )

    result = service.generate_direct(["/115/automv/Movie.mkv"])

    output = tmp_path / "115" / "automv" / "Movie.strm"
    assert result["created"] == [str(output)]
    assert output.read_text() == "http://alist.local/d/media115/automv/Movie.mkv"
