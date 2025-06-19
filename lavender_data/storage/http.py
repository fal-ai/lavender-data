import httpx
import os
import tqdm
from typing import Optional

from lavender_data.storage.abc import Storage


MULTIPART_CHUNKSIZE = 1 << 23


def http_download(
    remote_path: str,
    local_path: str,
    *,
    follow_redirects: bool = True,
    show_progress: bool = False,
) -> None:
    with httpx.stream("GET", remote_path, follow_redirects=follow_redirects) as r:
        content_length = r.headers.get("Content-Length")
        if content_length is not None:
            content_length = int(content_length)
        else:
            content_length = None

        progress = tqdm.tqdm(
            disable=not show_progress,
            desc=f"Downloading {remote_path}",
            total=content_length,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            leave=False,
        )
        with open(local_path, "wb") as f:
            for chunk in r.iter_bytes():
                progress.update(len(chunk))
                f.write(chunk)
        progress.close()


class HttpStorage(Storage):
    scheme = "http"

    def download(
        self,
        remote_path: str,
        local_path: str,
        *,
        follow_redirects: bool = True,
        show_progress: bool = False,
    ) -> None:
        http_download(
            remote_path,
            local_path,
            follow_redirects=follow_redirects,
            show_progress=show_progress,
        )

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

    def download(
        self,
        remote_path: str,
        local_path: str,
        *,
        follow_redirects: bool = True,
        show_progress: bool = False,
    ) -> None:
        http_download(
            remote_path,
            local_path,
            follow_redirects=follow_redirects,
            show_progress=show_progress,
        )

    def upload(self, local_path: str, remote_path: str) -> None:
        raise NotImplementedError

    def list(self, remote_path: str, limit: Optional[int] = None) -> list[str]:
        response = httpx.get(os.path.join(remote_path, "index.html"))
        if response.status_code != 200:
            raise ValueError(f"Failed to list {remote_path}")

        return [
            line.split(" ")[0] for line in response.text.split("\n") if line.strip()
        ]

    def get_url(self, remote_path: str) -> str:
        return remote_path
