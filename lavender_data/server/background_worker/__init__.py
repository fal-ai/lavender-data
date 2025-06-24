from typing import Annotated

from fastapi import Depends

from .background_worker import (
    TaskStatus,
    BackgroundWorker,
    get_background_worker,
    setup_background_worker,
)
from .memory import (
    SharedMemory,
    setup_shared_memory,
    get_shared_memory,
    shutdown_shared_memory,
)
from .process_pool import ProcessPool, pool_task

__all__ = [
    "TaskStatus",
    "BackgroundWorker",
    "get_background_worker",
    "setup_background_worker",
    "shutdown_background_worker",
    "CurrentBackgroundWorker",
    "CurrentSharedMemory",
    "SharedMemory",
    "setup_shared_memory",
    "get_shared_memory",
    "shutdown_shared_memory",
    "ProcessPool",
    "get_process_pool",
    "pool_task",
]


def shutdown_background_worker():
    get_background_worker().shutdown()


def get_process_pool():
    return get_background_worker().process_pool()


CurrentBackgroundWorker = Annotated[BackgroundWorker, Depends(get_background_worker)]
CurrentSharedMemory = Annotated[SharedMemory, Depends(get_shared_memory)]
