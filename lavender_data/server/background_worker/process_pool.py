import time
import uuid
import os
import signal
import threading
import multiprocessing as mp
from typing import Optional, Any, NamedTuple
import traceback


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
    setup_registries(
        settings.lavender_data_modules_dir,
        settings.lavender_data_modules_reload_interval,
    )
    setup_reader(settings.lavender_data_reader_disk_cache_size)

    def _abort_on_kill_switch():
        while True:
            if kill_switch.is_set():
                os.kill(os.getpid(), signal.SIGTERM)
            time.sleep(0.1)

    threading.Thread(target=_abort_on_kill_switch, daemon=True).start()


class WorkItem(NamedTuple):
    work_id: str
    func: str
    kwargs: dict


class ResultItem(NamedTuple):
    work_id: str
    result: Optional[Any] = None
    exception: Optional[str] = None


STOP_SIGN = "STOP"


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

    while not kill_switch.is_set():
        work_item = None
        try:
            work_item = call_queue.get()
            if work_item == STOP_SIGN:
                break
        except EOFError:
            logger.debug("Call queue closed, exiting worker process")
            break

        try:
            result = _tasks[work_item.func](**work_item.kwargs)
            result_item = ResultItem(work_id=work_item.work_id, result=result)
        except Exception as e:
            logger.exception(f"Error processing work {work_item.work_id}: {e}")
            result_item = ResultItem(
                work_id=work_item.work_id,
                exception="".join(
                    traceback.format_exception(type(e), e, e.__traceback__)
                )
                + "\n"
                + "".join(traceback.format_tb(e.__traceback__)),
            )

        result_queue.put(result_item)

    if work_item is not None:
        result_queue.put(
            ResultItem(
                work_id=work_item.work_id,
                exception="Aborted",
            )
        )
        logger.warning(f"work {work_item.work_id} aborted")

    logger.debug("_worker_process exiting")


def _clear_queue(queue: mp.Queue) -> list[Any]:
    is_macos = False
    try:
        queue.qsize()
    except NotImplementedError:
        is_macos = True

    items = []

    if is_macos:
        while not queue.empty():
            time.sleep(0.001)
            items.append(queue.get())
    else:
        while not queue.empty():
            items.append(queue.get())

    return items


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
        self._call_queue = self._mp_ctx.Queue()
        self._result_queue = self._mp_ctx.Queue()

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

        self._spawner_thread = threading.Thread(
            target=self._spawner_thread, daemon=True
        )
        self._spawner_thread.start()

        self._manager_thread = threading.Thread(
            target=self._manager_thread, daemon=True
        )
        self._manager_thread.start()

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

    def _spawner_thread(self):
        while not self._kill_switch.is_set():
            for p in self._processes:
                if not p.is_alive():
                    self._logger.warning(f"process {p.pid} died, spawning a new one")
                    self._processes.remove(p)
                    self._spawn_worker(1)
            time.sleep(0.1)

        self._logger.debug("_spawner_thread exiting")

    def _manager_thread(self):
        while not self._kill_switch.is_set():
            try:
                result = self._result_queue.get()
                if result == STOP_SIGN:
                    break
            except (EOFError, OSError):
                break
            except TypeError as e:
                if "NoneType" in str(e):
                    break
                raise e

            work_id = result.work_id
            with self._tasks_result_lock:
                if result.result is not None or result.exception is not None:
                    self._tasks_result[work_id] = result

            if work_id in self._tasks_completed:
                self._tasks_completed[work_id].set()
                del self._tasks_completed[work_id]
            else:
                self._logger.warning(f"Work {work_id} not found in _tasks_completed")

        self._logger.debug("_manager_thread exiting")

    def submit(
        self,
        func,
        work_id: Optional[str] = None,
        cancel_on_duplicate: bool = False,
        **kwargs,
    ):
        if not hasattr(func, "_task_name") or func._task_name not in _tasks:
            raise ValueError(f"Function {func.__name__} is not a pool task")

        work_id = work_id or str(uuid.uuid4())
        if work_id in self._tasks_completed:
            if cancel_on_duplicate:
                self.cancel(work_id)
            else:
                return work_id

        work_item = WorkItem(work_id=work_id, func=func._task_name, kwargs=kwargs)

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

    def as_completed(
        self,
        work_ids: list[str],
        interval: float = 0.01,
        timeout: Optional[float] = None,
    ):
        _work_ids = work_ids.copy()
        start = time.time()
        while len(_work_ids) > 0 and (timeout is None or time.time() - start < timeout):
            for work_id in _work_ids:
                if work_id in self._tasks_completed:
                    continue
                _work_ids.remove(work_id)
                yield self.result(work_id)
            if self._kill_switch.is_set():
                break
            time.sleep(interval)

        if len(_work_ids) > 0:
            raise TimeoutError(f"Work {_work_ids} have no result in {timeout} seconds")

    def cancel(self, *work_ids: str):
        if len(work_ids) == 0:
            return

        cancelled_work_ids = []
        work_items = []

        items = _clear_queue(self._call_queue)
        for work_item in items:
            if work_item.work_id in work_ids:
                cancelled_work_ids.append(work_item.work_id)
            else:
                work_items.append(work_item)

        self._logger.debug(f"Cancelled {len(cancelled_work_ids)} tasks")
        self._logger.debug(f"Remaining {len(work_items)} tasks")

        for work_item in work_items:
            self._call_queue.put(work_item)

        for work_id in cancelled_work_ids:
            if work_id in self._tasks_completed:
                self._tasks_completed[work_id].set()
                del self._tasks_completed[work_id]

    def shutdown(self):
        self._kill_switch.set()
        self._spawner_thread.join()

        _clear_queue(self._call_queue)
        for p in self._processes:
            self._call_queue.put(STOP_SIGN)
        self._call_queue.close()

        _clear_queue(self._result_queue)
        self._result_queue.put(STOP_SIGN)
        self._result_queue.close()

        self._manager_thread.join()

        for p in self._processes:
            p.join()


_tasks = {}


def pool_task(name: Optional[str] = None, **others):
    def _wrapper(func):
        func._task_name = name or func.__name__
        func._task_kwargs = others
        _tasks[func._task_name] = func
        return func

    return _wrapper
