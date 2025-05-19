import time
import uuid
import os
import signal
import threading
import multiprocessing as mp
from typing import Callable, Optional, Any
import traceback

from pydantic import BaseModel

from lavender_data.server.settings import get_settings, Settings
from lavender_data.server.db import setup_db
from lavender_data.server.cache import setup_cache
from lavender_data.server.reader import setup_reader
from lavender_data.server.registries import setup_registries
from lavender_data.logging import get_logger


def _initializer(settings: Settings, kill_switch):
    import sys

    os.environ["LAVENDER_DATA_IS_WORKER"] = "true"
    f = open(os.devnull, "w")
    sys.stderr = f
    sys.stdout = f

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


class WorkItem(BaseModel):
    work_id: str
    func: Callable
    kwargs: dict


class ResultItem(BaseModel):
    work_id: str
    result: Optional[Any] = None
    exception: Optional[str] = None


def _worker_process(
    settings: Settings,
    ready,
    error,
    kill_switch,
    call_queue,
    result_queue,
):
    try:
        _initializer(settings, kill_switch)
    except Exception as e:
        error.put(
            str(e)
            + "\n"
            + "".join(traceback.format_exception(type(e), e, e.__traceback__))
        )
        raise e

    ready.set()

    logger = get_logger(__name__)

    work_item = None
    try:
        while not kill_switch.is_set():
            work_item = call_queue.get()

            try:
                result = work_item.func(**work_item.kwargs)
                result_item = ResultItem(work_id=work_item.work_id, result=result)
            except Exception as e:
                result_item = ResultItem(
                    work_id=work_item.work_id,
                    exception="".join(
                        traceback.format_exception(type(e), e, e.__traceback__)
                    )
                    + "\n"
                    + "".join(traceback.format_tb(e.__traceback__)),
                )

            result_queue.put(result_item)

    except KeyboardInterrupt:
        pass

    if work_item is not None:
        result_queue.put(
            ResultItem(
                work_id=work_item.work_id,
                exception="Aborted",
            )
        )
        logger.warning(f"work {work_item.work_id} aborted")


class _ExceptionFromWorker(Exception):
    def __init__(self, exception: str):
        self.exception = exception

    def __str__(self):
        return self.exception

    def __repr__(self):
        return self.exception


class ProcessPool:
    def __init__(self, num_workers: int):
        self._logger = get_logger(__name__)

        self._mp_ctx = mp.get_context("spawn")
        self._kill_switch = self._mp_ctx.Event()
        self._call_queue = self._mp_ctx.SimpleQueue()
        self._result_queue = self._mp_ctx.SimpleQueue()

        self._num_workers = num_workers
        self._processes: list[mp.Process] = []
        self._tasks_completed = {}

        # TODO clean up thread
        self._tasks_result: dict[str, ResultItem] = {}
        self._tasks_result_lock = threading.Lock()

        self._logger.debug(
            f"Starting background worker with {self._num_workers} workers"
        )
        self._spawn_worker(self._num_workers)
        self._logger.debug(f"Spawned {len(self._processes)} workers")
        self._start_manager_thread()

    def _spawn_worker(self, num_processes: int = 1, timeout: float = 60):
        events = [
            (self._mp_ctx.Event(), self._mp_ctx.Queue()) for _ in range(num_processes)
        ]
        for i in range(num_processes):
            ready, error = events[i]
            p = self._mp_ctx.Process(
                target=_worker_process,
                args=(
                    get_settings(),
                    ready,
                    error,
                    self._kill_switch,
                    self._call_queue,
                    self._result_queue,
                ),
                daemon=True,
            )
            p.start()
            self._processes.append(p)

        ready = False
        error = None
        start = time.time()
        while not ready and not error and time.time() - start < timeout:
            ready = all(ready.is_set() for ready, _ in events)
            for _, e in events:
                try:
                    error = e.get(block=False, timeout=0)
                except:
                    pass

            time.sleep(0.1)

        if error:
            raise RuntimeError(f"Failed to spawn {num_processes} workers: {error}")

        if not ready:
            raise TimeoutError(
                f"Failed to spawn {num_processes} workers in {timeout} seconds"
            )

        return p

    def _start_keep_process_count_thread(self):
        def _keep_process_count_thread():
            while not self._kill_switch.is_set():
                for p in self._processes:
                    if not p.is_alive():
                        self._logger.warning(
                            f"process {p.pid} died, spawning a new one"
                        )
                        self._processes.remove(p)
                        self._spawn_worker(1)
                time.sleep(0.1)

            for p in self._processes:
                p.terminate()

        threading.Thread(target=_keep_process_count_thread, daemon=True).start()

    def _start_manager_thread(self):
        def _manager_thread():
            while not self._kill_switch.is_set():
                try:
                    result: ResultItem = self._result_queue.get()
                except EOFError:
                    self._logger.debug("Result queue closed, exiting manager thread")
                    break

                work_id = result.work_id
                with self._tasks_result_lock:
                    if result.result is not None or result.exception is not None:
                        self._tasks_result[work_id] = result

                if work_id in self._tasks_completed:
                    self._tasks_completed[work_id].set()
                    del self._tasks_completed[work_id]
                else:
                    self._logger.warning(
                        f"Work {work_id} not found in _tasks_completed"
                    )

        threading.Thread(target=_manager_thread, daemon=True).start()

    def submit(
        self,
        func,
        **kwargs,
    ):
        work_id = str(uuid.uuid4())
        work_item = WorkItem(work_id=work_id, func=func, kwargs=kwargs)

        self._tasks_completed[work_item.work_id] = threading.Event()
        self._call_queue.put(work_item)

        return work_id

    def result(self, work_id: str):
        if work_id in self._tasks_completed:
            self._tasks_completed[work_id].wait()

        if work_id not in self._tasks_result:
            raise ValueError(f"Work {work_id} have no result")

        with self._tasks_result_lock:
            result = self._tasks_result.pop(work_id)
            if result.exception is not None:
                raise _ExceptionFromWorker(result.exception)

            return result.result

    def shutdown(self):
        self._kill_switch.set()
        self._call_queue.close()
        self._result_queue.close()
        for p in self._processes:
            p.terminate()
        for p in self._processes:
            p.kill()
        for p in self._processes:
            p.join()
