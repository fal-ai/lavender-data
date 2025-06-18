import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from lavender_data.logging import get_logger
from lavender_data.storage.abc import Storage
from lavender_data.storage.s3 import S3Storage
from lavender_data.storage.hf import HuggingfaceStorage
from lavender_data.storage.file import LocalFileStorage
from lavender_data.storage.http import HttpStorage, HttpsStorage

__all__ = [
    "Storage",
    "S3Storage",
    "HuggingfaceStorage",
    "LocalFileStorage",
    "HttpStorage",
    "HttpsStorage",
    "download_file",
    "upload_file",
    "list_files",
]


def _download_file_with_timeout(
    remote_path: str,
    local_path: str,
    *,
    timeout: int,
):
    executor = ThreadPoolExecutor()
    try:
        storage = Storage.get(remote_path)
        future = executor.submit(storage.download, remote_path, local_path)
        return future.result(timeout=timeout)
    except RuntimeError as e:
        if "cannot schedule new futures after" in str(e):
            # shutdown
            return
        raise e
    except TimeoutError as e:
        future.cancel()
        raise e


def _download_file_with_retry(
    remote_path: str,
    local_path: str,
    *,
    timeout: int,
    retry: int,
    backoff: float,
    warn_on_retry: bool,
):
    for i in range(retry + 1):
        try:
            return _download_file_with_timeout(remote_path, local_path, timeout=timeout)
        except FileNotFoundError as e:
            raise e
        except Exception as e:
            if i < retry:
                if warn_on_retry:
                    get_logger(__name__).warning(
                        f"Failed to download file {remote_path} to {local_path}: {e}, retrying... ({i+1}/{retry})"
                    )
                time.sleep(backoff)
            else:
                raise e


def download_file(
    remote_path: str,
    local_path: str,
    *,
    timeout: int = 60,
    retry: int = 3,
    backoff: float = 3,
    warn_on_retry: bool = True,
):
    _download_file_with_retry(
        remote_path,
        local_path,
        timeout=timeout,
        retry=retry,
        backoff=backoff,
        warn_on_retry=warn_on_retry,
    )
    return local_path


def _upload_file_with_timeout(
    local_path: str,
    remote_path: str,
    *,
    timeout: int,
) -> None:
    executor = ThreadPoolExecutor()
    try:
        storage = Storage.get(remote_path)
        future = executor.submit(storage.upload, local_path, remote_path)
        future.result(timeout=timeout)
    except RuntimeError as e:
        if "cannot schedule new futures after" in str(e):
            # shutdown
            return
        raise e
    except TimeoutError as e:
        future.cancel()
        raise e


def _upload_file_with_retry(
    local_path: str,
    remote_path: str,
    *,
    timeout: int,
    retry: int,
    backoff: float,
    warn_on_retry: bool,
) -> None:
    for i in range(retry + 1):
        try:
            _upload_file_with_timeout(local_path, remote_path, timeout=timeout)
            return
        except FileNotFoundError as e:
            raise e
        except Exception as e:
            if i < retry:
                if warn_on_retry:
                    get_logger(__name__).warning(
                        f"Failed to upload file {local_path} to {remote_path}: {e}, retrying... ({i+1}/{retry})"
                    )
                time.sleep(backoff)
            else:
                raise e


def upload_file(
    local_path: str,
    remote_path: str,
    *,
    timeout: int = 60,
    retry: int = 3,
    backoff: float = 3,
    delete_after_upload: bool = False,
    warn_on_retry: bool = True,
):
    _upload_file_with_retry(
        local_path,
        remote_path,
        timeout=timeout,
        retry=retry,
        backoff=backoff,
        warn_on_retry=warn_on_retry,
    )
    if delete_after_upload and not remote_path.startswith("file://"):
        try:
            os.remove(local_path)
        except Exception as e:
            get_logger(__name__).warning(
                f"Failed to delete file {local_path} after upload: {e}"
            )


def list_files(remote_path: str, limit: Optional[int] = None) -> list[str]:
    # TODO timeout
    storage = Storage.get(remote_path)
    return storage.list(remote_path, limit)


def get_url(remote_path: str) -> str:
    storage = Storage.get(remote_path)
    return storage.get_url(remote_path)
