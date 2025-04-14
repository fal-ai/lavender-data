import os
import time
from concurrent.futures import ThreadPoolExecutor

from lavender_data.logging import get_logger
from lavender_data.storage.abc import Storage
from lavender_data.storage.s3 import S3Storage
from lavender_data.storage.hf import HuggingfaceStorage
from lavender_data.storage.file import LocalFileStorage

__all__ = [
    "Storage",
    "S3Storage",
    "HuggingfaceStorage",
    "LocalFileStorage",
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
    with ThreadPoolExecutor() as executor:
        storage = Storage.get(remote_path)
        future = executor.submit(storage.download, remote_path, local_path)
        try:
            return future.result(timeout=timeout)
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
):
    logger = get_logger(__name__)
    for i in range(retry):
        try:
            return _download_file_with_timeout(remote_path, local_path, timeout=timeout)
        except Exception as e:
            if i < retry - 1:
                logger.warning(
                    f"Failed to download file {remote_path} to {local_path}: {e}, retrying... ({i}/{retry})"
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
):
    _download_file_with_retry(
        remote_path, local_path, timeout=timeout, retry=retry, backoff=backoff
    )
    return local_path


def _upload_file_with_timeout(
    local_path: str,
    remote_path: str,
    *,
    timeout: int,
) -> None:
    with ThreadPoolExecutor() as executor:
        storage = Storage.get(remote_path)
        future = executor.submit(storage.upload, local_path, remote_path)
        try:
            future.result(timeout=timeout)
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
) -> None:
    logger = get_logger(__name__)
    for i in range(retry):
        try:
            _upload_file_with_timeout(local_path, remote_path, timeout=timeout)
            return
        except Exception as e:
            if i < retry - 1:
                logger.warning(
                    f"Failed to upload file {local_path} to {remote_path}: {e}, retrying... ({i}/{retry})"
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
):
    logger = get_logger(__name__)
    _upload_file_with_retry(
        local_path, remote_path, timeout=timeout, retry=retry, backoff=backoff
    )
    if delete_after_upload and not remote_path.startswith("file://"):
        try:
            os.remove(local_path)
        except Exception as e:
            logger.warning(f"Failed to delete file {local_path} after upload: {e}")


def list_files(remote_path: str) -> list[str]:
    storage = Storage.get(remote_path)
    return storage.list(remote_path)
