from typing import Annotated

from fastapi import Depends

from .worker import BackgroundWorker, TaskMetadata, TaskStatus
from .memory import Memory


background_worker: BackgroundWorker = None


def setup_background_worker(num_workers: int):
    global background_worker
    background_worker = BackgroundWorker(num_workers)


def get_background_worker():
    global background_worker
    if background_worker is None:
        raise RuntimeError("Background worker not initialized")

    return background_worker


def get_background_worker_memory():
    return get_background_worker().memory()


def shutdown_background_worker():
    get_background_worker().shutdown()


CurrentBackgroundWorker = Annotated[BackgroundWorker, Depends(get_background_worker)]
CurrentBackgroundWorkerMemory = Annotated[Memory, Depends(get_background_worker_memory)]
