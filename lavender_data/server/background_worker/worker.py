import time
import uuid
import os
import signal
import threading
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, Future
from concurrent.futures.process import BrokenProcessPool
from datetime import datetime, UTC
from typing import Callable, Optional, Any

from pydantic import BaseModel

from lavender_data.server.background_worker.memory import Memory, TaskStatus
from lavender_data.server.settings import get_settings, Settings
from lavender_data.server.db import setup_db
from lavender_data.server.cache import setup_cache
from lavender_data.server.reader import setup_reader
from lavender_data.server.registries import setup_registries
from lavender_data.logging import get_logger


class TaskMetadata(BaseModel):
    uid: str
    name: str
    start_time: datetime
    kwargs: dict
    status: Optional[TaskStatus] = None


class BackgroundWorker:
    def __init__(self, num_workers: int):
        self._logger = get_logger(__name__)
        self._mp_ctx = mp.get_context("spawn")
        self._kill_switch = self._mp_ctx.Event()
        self._num_workers = num_workers if num_workers > 0 else mp.cpu_count()
        self._logger.debug(
            f"Starting background worker with {self._num_workers} workers"
        )
        self._executor = ProcessPoolExecutor(
            self._num_workers,
            mp_context=self._mp_ctx,
            initializer=BackgroundWorker._initializer,
            initargs=(get_settings(), self._kill_switch),
        )
        self._memory = Memory()
        self._tasks: list[tuple[TaskMetadata, Future]] = []
        self._tasks_lock = threading.Lock()

        self._start_cleanup_thread()

    @staticmethod
    def _initializer(settings: Settings, kill_switch):
        setup_db(settings.lavender_data_db_url)
        setup_cache(redis_url=settings.lavender_data_redis_url)
        setup_registries(settings.lavender_data_modules_dir)
        setup_reader(settings.lavender_data_reader_disk_cache_size)

        def _abort_on_kill_switch():
            while True:
                if kill_switch.is_set():
                    os.kill(os.getpid(), signal.SIGTERM)
                time.sleep(0.1)

        threading.Thread(target=_abort_on_kill_switch, daemon=True).start()

    def _cleanup_tasks(self):
        with self._tasks_lock:
            for e in self._tasks:
                _, future = e
                if future.done():
                    self._tasks.remove(e)

    def _start_cleanup_thread(self):
        def _cleanup_tasks():
            while True:
                time.sleep(1)
                self._cleanup_tasks()

        threading.Thread(target=_cleanup_tasks, daemon=True).start()

    def running_tasks(self) -> list[TaskMetadata]:
        self._cleanup_tasks()
        with self._tasks_lock:
            tasks = [t[0] for t in self._tasks]
            tasks.sort(key=lambda t: t.start_time)
            for task in tasks:
                task.status = self._memory.get_task_status(task.uid)
            return tasks

    def submit(
        self,
        func,
        task_uid: Optional[str] = None,
        task_name: Optional[str] = None,
        on_complete: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Any], None]] = None,
        **kwargs,
    ):
        task_uid = task_uid or str(uuid.uuid4())
        future = self._executor.submit(
            func,
            **kwargs,
            memory=self._memory,
            task_uid=task_uid,
        )

        def on_done(future: Future):
            try:
                result = future.result(timeout=0.1)
                self._memory.set_task_status(
                    task_uid, status="completed", ex=24 * 60 * 60
                )
                self._cleanup_tasks()
                if on_complete is not None:
                    on_complete(result)
            except BrokenProcessPool:
                if self._kill_switch.is_set():
                    # The process pool was killed, so we don't need to do anything
                    return
                else:
                    raise
            except Exception as e:
                if on_error is not None:
                    on_error(e)

        future.add_done_callback(on_done)

        with self._tasks_lock:
            self._tasks.append(
                (
                    TaskMetadata(
                        uid=task_uid,
                        name=task_name or func.__name__,
                        start_time=datetime.now(UTC),
                        kwargs=kwargs,
                    ),
                    future,
                )
            )

        self._memory.set_task_status(task_uid, status="pending", current=0, total=0)

        return task_uid

    def wait(self, task_uid: str):
        task = next((t for t in self._tasks if t[0].uid == task_uid), None)
        if task is None:
            return

        _, future = task
        future.result()

    def cancel(self, task_uid: str):
        with self._tasks_lock:
            task = next((t for t in self._tasks if t[0].uid == task_uid), None)
            if task is None:
                return

            _, future = task
            cancelled = future.cancel()
            if cancelled:
                self._tasks.remove(task)

            # abort

    def shutdown(self):
        self._logger.debug("Shutting down background worker")
        self._executor.shutdown(wait=False)
        self._kill_switch.set()
        self._memory.clear()
        self._logger.debug("Shutdown complete")

    def memory(self) -> Memory:
        return self._memory
