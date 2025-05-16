from typing import Annotated

from fastapi import Depends

from .background_worker import (
    TaskStatus,
    TaskMetadata,
    BackgroundWorker,
    get_background_worker,
    setup_background_worker,
)
from .memory import SharedMemory
from .process_pool import ProcessPool

__all__ = [
    "TaskStatus",
    "TaskMetadata",
    "BackgroundWorker",
    "get_background_worker",
    "setup_background_worker",
    "shutdown_background_worker",
    "CurrentBackgroundWorker",
    "SharedMemory",
    "get_shared_memory",
    "ProcessPool",
    "get_process_pool",
]


def shutdown_background_worker():
    get_background_worker().shutdown()


def get_shared_memory():
    return get_background_worker().memory()


def get_process_pool():
    return get_background_worker().process_pool()


CurrentBackgroundWorker = Annotated[BackgroundWorker, Depends(get_background_worker)]
