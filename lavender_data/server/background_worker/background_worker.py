import time
import json
import uuid
import threading
import os
from concurrent.futures import ThreadPoolExecutor, Future

from typing import Callable, Optional, NamedTuple

from pydantic import BaseModel

from lavender_data.server.cache import get_cache
from lavender_data.server.background_worker.process_pool import ProcessPool
from lavender_data.logging import get_logger


class TaskStatus(BaseModel):
    status: str
    current: int
    total: int


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

    next(get_cache()).hset(
        f"background-worker:tasks",
        task_id,
        json.dumps(
            {
                "status": status if status is not None else _status.status,
                "current": current if current is not None else _status.current,
                "total": total if total is not None else _status.total,
            }
        ),
    )


def get_task_status(task_uid: str) -> Optional[TaskStatus]:
    status = next(get_cache()).hget(f"background-worker:tasks", task_uid)
    if status is None:
        return None

    try:
        status = json.loads(status)
    except Exception:
        return None

    return TaskStatus.model_validate(status)


def delete_task_status(task_uid: str):
    next(get_cache()).hdel(f"background-worker:tasks", task_uid)


def all_task_statuses() -> dict[str, TaskStatus]:
    tasks = next(get_cache()).hgetall(f"background-worker:tasks")
    return {
        task_id: TaskStatus.model_validate(json.loads(t))
        for task_id, t in tasks.items()
    }


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
    status_ex = 10 * 60
    try:
        set_task_status(task_id, status="running", ex=status_ex)
        generator = func(*args, **kwargs)
        for status in generator:
            if abort_event.is_set():
                generator.close()
                raise Aborted()

            if not isinstance(status, TaskStatus):
                continue

            set_task_status(
                task_id,
                status=status.status,
                total=status.total,
                current=status.current,
                ex=status_ex,
            )

        set_task_status(task_id, status="completed", ex=status_ex)
        logger.debug(f"Task {task_id} completed")
    except Aborted:
        set_task_status(task_id, status="aborted", ex=status_ex)
        logger.info(f"Task {task_id} aborted")
    except Exception as e:
        set_task_status(task_id, status="failed", ex=status_ex)
        logger.exception(f"Error running task {task_id}: {e}")


def _run_task_no_status(
    func: Callable,
    task_id: str,
    abort_event: threading.Event,
    *args,
    **kwargs,
):
    logger = get_logger(__name__)
    try:
        for _ in func(*args, **kwargs):
            if abort_event.is_set():
                raise Aborted()
    except Exception as e:
        logger.exception(f"Error running task {task_id}: {e}")


class TaskItem(NamedTuple):
    future: Future
    abort_event: threading.Event


class BackgroundWorker:
    def __init__(self, num_workers: int):
        self._logger = get_logger(__name__)
        self._num_workers = num_workers if num_workers > 0 else (os.cpu_count() or 1)

        self._process_pool = ProcessPool(self._num_workers)

        self._executor = ThreadPoolExecutor(self._num_workers)
        self._abort_events: dict[str, threading.Event] = {}
        self._futures: dict[str, Future] = {}

        self._start_cleanup_thread()

    def process_pool(self) -> ProcessPool:
        return self._process_pool

    def _cleanup_tasks(self):
        for task_id, status in all_task_statuses().items():
            if status.status == "completed":
                delete_task_status(task_id)

            if status.status in ["completed", "aborted", "failed"]:
                self._abort_events.pop(task_id, None)
                self._futures.pop(task_id, None)

    def _start_cleanup_thread(self):
        def _cleanup_tasks():
            while True:
                time.sleep(10)
                self._cleanup_tasks()

        threading.Thread(target=_cleanup_tasks, daemon=True).start()

    def list_tasks(self) -> dict[str, TaskStatus]:
        self._cleanup_tasks()
        return {task_id: status for task_id, status in all_task_statuses().items()}

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        return get_task_status(task_id)

    def thread_pool_submit(
        self,
        func: Callable,
        task_id: Optional[str] = None,
        task_name: Optional[str] = None,
        with_status: bool = False,
        abort_on_duplicate: bool = False,
        **kwargs,
    ):
        task_id = task_id or str(uuid.uuid4())
        if with_status and get_task_status(task_id) is not None:
            if abort_on_duplicate:
                self.abort(task_id)
            else:
                return task_id

        abort_event = threading.Event()
        future = self._executor.submit(
            _run_task if with_status else _run_task_no_status,
            func,
            task_id,
            abort_event,
            **kwargs,
        )

        self._abort_events[task_id] = abort_event
        self._futures[task_id] = future

        return task_id

    def process_pool_submit(
        self,
        func: Callable,
        **kwargs,
    ):
        return self.process_pool().submit(func, **kwargs)

    def abort(self, task_id: str):
        status = get_task_status(task_id)
        if status is not None:
            delete_task_status(task_id)

        if task_id in self._abort_events:
            self._abort_events[task_id].set()

        if task_id in self._futures:
            self._futures[task_id].cancel()

    def abort_all(self):
        for task_id, status in all_task_statuses().items():
            if status.status == "running":
                self.abort(task_id)

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
