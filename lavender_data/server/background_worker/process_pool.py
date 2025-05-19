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
    exception_msg: Optional[str] = None
    exception_traceback: Optional[str] = None


def _worker_process(settings: Settings, kill_switch, call_queue, result_queue):
    os.environ["LAVENDER_DATA_IS_WORKER"] = "true"

    _initializer(settings, kill_switch)

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
                    exception_msg=str(e),
                    exception_traceback="".join(
                        traceback.format_exception(type(e), e, e.__traceback__)
                    ),
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


class ProcessPool:
    def __init__(self, num_workers: int):
        self._logger = get_logger(__name__)

        self._mp_ctx = mp.get_context("spawn")
        self._kill_switch = self._mp_ctx.Event()
        self._call_queue = self._mp_ctx.SimpleQueue()
        self._result_queue = self._mp_ctx.SimpleQueue()

        self._num_workers = num_workers
        self._logger.debug(
            f"Starting background worker with {self._num_workers} workers"
        )

        self._processes: list[mp.Process] = []

        for _ in range(self._num_workers):
            self._spawn_worker()

        self._tasks_completed = {}

        self._tasks_callbacks: dict[str, Callable[[ResultItem], None]] = {}
        self._tasks_callbacks_lock = threading.Lock()

        self._start_manager_thread()

    def _spawn_worker(self):
        p = self._mp_ctx.Process(
            target=_worker_process,
            args=(
                get_settings(),
                self._kill_switch,
                self._call_queue,
                self._result_queue,
            ),
            daemon=True,
        )
        p.start()
        self._processes.append(p)
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
                        self._spawn_worker()
                time.sleep(0.1)

            for p in self._processes:
                p.terminate()

        threading.Thread(target=_keep_process_count_thread, daemon=True).start()

    def _start_manager_thread(self):
        def _manager_thread():
            while not self._kill_switch.is_set():
                try:
                    result = self._result_queue.get()
                except EOFError:
                    self._logger.debug("Result queue closed, exiting manager thread")
                    break

                with self._tasks_callbacks_lock:
                    callback = self._tasks_callbacks.get(result.work_id)
                    if callback is None:
                        continue

                    if result.work_id in self._tasks_completed:
                        self._tasks_completed[result.work_id].set()
                        del self._tasks_completed[result.work_id]
                    else:
                        self._logger.warning(
                            f"Work {result.work_id} not found in _tasks_completed"
                        )

                    try:
                        callback(result)
                    except Exception as e:
                        self._logger.exception(
                            f"Error calling callback for work {result.work_id}: {e}"
                        )

                    del self._tasks_callbacks[result.work_id]

        threading.Thread(target=_manager_thread, daemon=True).start()

    def submit(
        self,
        func,
        on_complete: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[str, str], None]] = None,
        **kwargs,
    ):
        work_id = str(uuid.uuid4())
        work_item = WorkItem(work_id=work_id, func=func, kwargs=kwargs)

        def callback(result_item: ResultItem):
            r = result_item.result
            e_msg = result_item.exception_msg
            e_tb = result_item.exception_traceback
            if on_complete is not None and r is not None:
                on_complete(r)
            if on_error is not None and e_msg is not None and e_tb is not None:
                on_error(e_msg, e_tb)

        with self._tasks_callbacks_lock:
            self._tasks_callbacks[work_item.work_id] = callback

        self._tasks_completed[work_item.work_id] = threading.Event()
        self._call_queue.put(work_item)

        return work_id

    def wait(self, *work_ids: str):
        for work_id in work_ids:
            if work_id not in self._tasks_completed:
                continue

            self._tasks_completed[work_id].wait()

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
