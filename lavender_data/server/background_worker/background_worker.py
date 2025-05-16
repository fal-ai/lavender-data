import time
import json
import uuid
import threading
import os
from concurrent.futures import ThreadPoolExecutor, Future

from datetime import datetime, UTC
from typing import Callable, Optional, NamedTuple

from pydantic import BaseModel

from lavender_data.server.cache import get_cache
from lavender_data.server.background_worker.process_pool import ProcessPool
from lavender_data.logging import get_logger


class TaskStatus(BaseModel):
    status: str
    current: int
    total: int


class TaskMetadata(BaseModel):
    uid: str
    name: str
    start_time: datetime
    kwargs: dict
    status: Optional[TaskStatus] = None


def set_task_status(
    task_id: str,
    status: Optional[str] = None,
    current: Optional[int] = None,
    total: Optional[int] = None,
    ex: Optional[int] = None,
):
    _status = get_task_status(task_id)
    if _status is None:
        _status = TaskStatus(status="", current=0, total=0)

    next(get_cache()).set(
        f"task-{task_id}",
        json.dumps(
            {
                "status": (status if status is not None else _status.status),
                "current": (current if current is not None else _status.current),
                "total": total if total is not None else _status.total,
            }
        ),
        ex=ex,
    )


def get_task_status(task_uid: str) -> Optional[TaskStatus]:
    status = next(get_cache()).get(f"task-{task_uid}")
    if status is None:
        return None

    try:
        status = json.loads(status)
    except Exception:
        return None

    return TaskStatus.model_validate(status)


def delete_task_status(task_uid: str):
    next(get_cache()).delete(f"task-{task_uid}")


class Aborted(Exception):
    pass


def _run_task(
    func: Callable,
    task_id: str,
    abort_event: threading.Event,
    *args,
    **kwargs,
):
    logger = get_logger(__name__)
    try:
        set_task_status(task_id, status="running", ex=24 * 60 * 60)
        for status in func(*args, **kwargs):
            set_task_status(
                task_id,
                status=status.status,
                total=status.total,
                current=status.current,
                ex=24 * 60 * 60,
            )
            if abort_event.is_set():
                raise Aborted()

        set_task_status(task_id, status="completed", ex=24 * 60 * 60)
    except Aborted:
        set_task_status(task_id, status="aborted", ex=24 * 60 * 60)
    except Exception as e:
        set_task_status(task_id, status="failed", ex=24 * 60 * 60)
        logger.exception(f"Error running task {task_id}: {e}")


class TaskItem(NamedTuple):
    metadata: TaskMetadata
    future: Future
    abort_event: threading.Event


class BackgroundWorker:
    def __init__(self, num_workers: int):
        self._logger = get_logger(__name__)
        self._num_workers = num_workers if num_workers > 0 else (os.cpu_count() or 1)

        self._process_pool = ProcessPool(self._num_workers)

        self._tasks: list[TaskItem] = []
        self._tasks_lock = threading.Lock()

        self._task_status: dict[str, TaskStatus] = {}

        self._executor = ThreadPoolExecutor(self._num_workers)

        self._start_cleanup_thread()

    def process_pool(self) -> ProcessPool:
        return self._process_pool

    def _cleanup_tasks(self):
        with self._tasks_lock:
            for t in self._tasks:
                if get_task_status(t.metadata.uid) is None:
                    self._tasks.remove(t)

    def _start_cleanup_thread(self):
        def _cleanup_tasks():
            while True:
                time.sleep(1)
                self._cleanup_tasks()

        threading.Thread(target=_cleanup_tasks, daemon=True).start()

    def running_tasks(self) -> list[TaskMetadata]:
        self._cleanup_tasks()
        with self._tasks_lock:
            tasks = [t.metadata for t in self._tasks]
            tasks.sort(key=lambda t: t.start_time)
            for task in tasks:
                task.status = get_task_status(task.uid)
            return tasks

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        return get_task_status(task_id)

    def submit(
        self,
        func: Callable,
        task_id: Optional[str] = None,
        task_name: Optional[str] = None,
        **kwargs,
    ):
        task_id = task_id or str(uuid.uuid4())

        abort_event = threading.Event()
        future = self._executor.submit(
            _run_task,
            func,
            task_id,
            abort_event,
            **kwargs,
        )

        with self._tasks_lock:
            self._tasks.append(
                TaskItem(
                    metadata=TaskMetadata(
                        uid=task_id,
                        name=task_name or func.__name__,
                        start_time=datetime.now(UTC),
                        kwargs=kwargs,
                    ),
                    future=future,
                    abort_event=abort_event,
                )
            )

        return task_id

    def abort(self, task_id: str):
        with self._tasks_lock:
            status = get_task_status(task_id)
            if status is not None:
                delete_task_status(task_id)

            task = next((t for t in self._tasks if t.metadata.uid == task_id), None)
            if task is not None:
                task.abort_event.set()
                task.future.cancel()
                self._tasks.remove(task)

    def abort_all(self):
        for t in self._tasks:
            self.abort(t.metadata.uid)

    def shutdown(self):
        self._logger.debug("Shutting down background worker")
        self.abort_all()
        self._executor.shutdown(wait=False)
        self.process_pool().shutdown()
        self._logger.debug("Shutdown complete")


# singleton
background_worker: BackgroundWorker = None


def setup_background_worker(num_workers: int):
    global background_worker
    background_worker = BackgroundWorker(num_workers)


def get_background_worker():
    global background_worker
    if background_worker is None:
        raise RuntimeError("Background worker not initialized")

    return background_worker
