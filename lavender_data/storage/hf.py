import urllib.parse
from pathlib import Path
from typing import Optional
from lavender_data.storage.abc import Storage


class HuggingfaceStorage(Storage):
    scheme = "hf"

    def __init__(self):
        try:
            from huggingface_hub import (
                utils,
                hf_hub_download,
                upload_file,
                list_repo_tree,
            )
        except ImportError:
            raise ImportError(
                "Please install required dependencies for HuggingfaceStorage. "
                "You can install them with `pip install lavender-data[hf]`"
            )

        utils.disable_progress_bars("huggingface_hub.http_get")
        utils.disable_progress_bars("huggingface_hub.http_post")

        self._download = hf_hub_download
        self._upload = upload_file
        self._list = list_repo_tree

    def _parse_remote_path(self, remote_path: str) -> tuple[str, str]:
        parsed = urllib.parse.urlparse(remote_path)
        org = parsed.netloc
        repo, path = parsed.path.lstrip("/").split("/", 1)
        repo_id = f"{org}/{repo}"
        return repo_id, path

    def download(self, remote_path: str, local_path: str) -> None:
        repo_id, path = self._parse_remote_path(remote_path)
        local_dir = Path(local_path).parent

        if not local_dir.exists():
            local_dir.mkdir(parents=True, exist_ok=True)

        self._download(
            repo_id=repo_id,
            filename=path,
            repo_type="dataset",
            local_dir=local_dir.as_posix(),
        )
        downloaded_path = Path(local_dir) / path
        if not downloaded_path.exists():
            raise FileNotFoundError(
                f"File not downloaded: {remote_path} -> {downloaded_path}"
            )

        if not downloaded_path.is_file():
            raise FileNotFoundError(f"Not a file: {remote_path} -> {downloaded_path}")

        downloaded_path.rename(local_path)

    def upload(self, local_path: str, remote_path: str) -> None:
        repo_id, path = self._parse_remote_path(remote_path)

        self._upload(
            repo_id=repo_id,
            repo_type="dataset",
            path_or_fileobj=local_path,
            path_in_repo=path,
        )

    def list(self, remote_path: str, limit: Optional[int] = None) -> list[str]:
        repo_id, path = self._parse_remote_path(remote_path)
        repo_files = self._list(repo_id, path, repo_type="dataset")
        _path = path.rstrip("/") + "/"
        return [file.path.removeprefix(_path) for file in repo_files]

    def get_url(self, remote_path: str) -> str:
        repo_id, path = self._parse_remote_path(remote_path)
        return f"https://huggingface.co/{repo_id}/resolve/{path}"
