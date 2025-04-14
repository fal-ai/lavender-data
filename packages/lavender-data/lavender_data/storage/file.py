import os
import shutil
from lavender_data.storage.abc import Storage

__all__ = ["LocalFileStorage"]


class LocalFileStorage(Storage):
    scheme = "file"

    def download(self, remote_path: str, local_path: str) -> None:
        _remote_path = remote_path.removeprefix("file://")
        os.makedirs(os.path.dirname(_remote_path), exist_ok=True)

        if _remote_path == local_path:
            return

        try:
            shutil.copy(os.path.abspath(_remote_path), local_path)
        except FileExistsError:
            pass

    def upload(self, local_path: str, remote_path: str) -> None:
        _remote_path = remote_path.removeprefix("file://")
        os.makedirs(os.path.dirname(_remote_path), exist_ok=True)

        if _remote_path == local_path:
            return

        try:
            shutil.copy(os.path.abspath(local_path), _remote_path)
        except FileExistsError:
            pass

    def list(self, remote_path: str) -> list[str]:
        _remote_path = remote_path.removeprefix("file://")
        return [f for f in os.listdir(_remote_path)]
