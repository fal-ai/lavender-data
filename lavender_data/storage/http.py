import httpx
import os
from pathlib import Path
from typing import Optional

from lavender_data.storage.abc import Storage


MULTIPART_CHUNKSIZE = 1 << 23


class HttpStorage(Storage):
    scheme = "http"

    def download(self, remote_path: str, local_path: str) -> None:
        with httpx.stream("GET", remote_path) as r:
            with open(local_path, "wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)

    def upload(self, local_path: str, remote_path: str) -> None:
        raise NotImplementedError

    def list(self, remote_path: str, limit: Optional[int] = None) -> list[str]:
        response = httpx.get(os.path.join(remote_path, "index.html"))
        if response.status_code != 200:
            raise ValueError(f"Failed to list {remote_path}")

        return [
            line.split(" ")[0] for line in response.text.split("\n") if line.strip()
        ]


class HttpsStorage(Storage):
    scheme = "https"

    def download(self, remote_path: str, local_path: str) -> None:
        with httpx.stream("GET", remote_path) as r:
            with open(local_path, "wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)

    def upload(self, local_path: str, remote_path: str) -> None:
        raise NotImplementedError

    def list(self, remote_path: str, limit: Optional[int] = None) -> list[str]:
        response = httpx.get(os.path.join(remote_path, "index.html"))
        if response.status_code != 200:
            raise ValueError(f"Failed to list {remote_path}")

        return [
            line.split(" ")[0] for line in response.text.split("\n") if line.strip()
        ]
