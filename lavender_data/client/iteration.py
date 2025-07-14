import time
import secrets
import queue
import traceback
import threading
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
import multiprocessing.shared_memory as mp_shared_memory
from typing import Optional, Union, Literal

from lavender_data.serialize import deserialize_sample, DeserializeException
from lavender_data.client.api import (
    get_client,
    LavenderDataClient,
    LavenderDataApiError,
    LavenderDataSampleProcessingError,
    IterationFilter,
    IterationPreprocessor,
    IterationCollater,
    IterationCategorizer,
)

__all__ = ["LavenderDataLoader"]


def noop_collate_fn(x):
    return x[0]


def _parse_registry_params(
    registry_name: Literal["filter", "preprocessor", "collater", "categorizer"],
    param: Union[tuple[str, dict], str],
):
    if isinstance(param, str):
        name = param
        params = {}
    elif isinstance(param, tuple) and len(param) == 2:
        name = param[0]
        params = param[1]
    else:
        raise ValueError(
            f"Incorrect parameter for {registry_name}: {param} (expected tuple[str, dict] or str)"
        )

    d = {"name": name, "params": params}
    if registry_name == "filter":
        return IterationFilter.from_dict(d)
    elif registry_name == "categorizer":
        return IterationCategorizer.from_dict(d)
    elif registry_name == "collater":
        return IterationCollater.from_dict(d)
    elif registry_name == "preprocessor":
        return IterationPreprocessor.from_dict(d)
    else:
        raise ValueError(f"Invalid registry name: {registry_name}")


def _api(api_url: Optional[str] = None, api_key: Optional[str] = None):
    if api_url is not None:
        return LavenderDataClient(api_url=api_url, api_key=api_key)
    else:
        return get_client()


class LavenderDataLoader:
    def __init__(
        self,
        dataset_id: Optional[str] = None,
        dataset_name: Optional[str] = None,
        shardsets: Optional[list[str]] = None,
        filters: Optional[list[Union[tuple[str, dict], str]]] = None,
        categorizer: Optional[Union[tuple[str, dict], str]] = None,
        collater: Optional[Union[tuple[str, dict], str]] = None,
        preprocessors: Optional[list[Union[tuple[str, dict], str]]] = None,
        max_retry_count: int = 0,
        skip_on_failure: bool = False,
        shuffle: Optional[bool] = None,
        shuffle_seed: Optional[int] = None,
        shuffle_block_size: Optional[int] = None,
        batch_size: Optional[int] = None,
        replication_pg: Optional[list[list[int]]] = None,
        rank: int = 0,
        world_size: Optional[int] = None,
        wait_participant_threshold: Optional[float] = None,
        iteration_id: Optional[str] = None,
        cluster_sync: bool = False,
        no_cache: bool = False,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        if iteration_id is None:
            if dataset_id is None:
                if dataset_name is None:
                    raise ValueError(
                        "Either dataset_id or dataset_name must be provided"
                    )
                dataset_id = _api(api_url, api_key).get_dataset(name=dataset_name).id

            iteration_response = _api(api_url, api_key).create_iteration(
                dataset_id=dataset_id,
                shardsets=shardsets,
                filters=(
                    [_parse_registry_params("filter", f) for f in filters]
                    if filters is not None
                    else None
                ),
                categorizer=(
                    _parse_registry_params("categorizer", categorizer)
                    if categorizer is not None
                    else None
                ),
                collater=(
                    _parse_registry_params("collater", collater)
                    if collater is not None
                    else None
                ),
                preprocessors=(
                    [_parse_registry_params("preprocessor", f) for f in preprocessors]
                    if preprocessors is not None
                    else None
                ),
                shuffle=shuffle,
                shuffle_seed=shuffle_seed,
                shuffle_block_size=shuffle_block_size,
                batch_size=batch_size,
                replication_pg=replication_pg,
                rank=rank,
                world_size=world_size,
                wait_participant_threshold=wait_participant_threshold,
                cluster_sync=cluster_sync,
            )
        else:
            iteration_response = _api(api_url, api_key).get_iteration(iteration_id)

        self._dataset_id = iteration_response.dataset_id
        self._iteration_id = iteration_response.id
        self._total = iteration_response.total

        self._using_indices = set()
        self._completed_indices = set()
        self._no_cache = no_cache
        self._max_retry_count = max_retry_count
        self._skip_on_failure = skip_on_failure
        self._rank = rank

        self._api_url = api_url
        self._api_key = api_key
        self._api = _api(self._api_url, self._api_key)

        self._bytes = 0
        self._started = False
        self._stopped = False

        self.id = self._iteration_id

        self._complete_thread: Optional[threading.Thread] = None

    def torch(
        self,
        *,
        num_workers: Optional[int] = None,
        prefetch_factor: Optional[int] = None,
        pin_memory_device: str = "",
        pin_memory: bool = False,
        timeout: float = 0,
        in_order: bool = True,
        poll_interval: float = 0.01,
        shm_size: int = 4 * 1024**2,
    ):
        try:
            from torch.utils.data import DataLoader
        except ImportError:
            raise ImportError("torch is not installed. Please install it first.")

        is_async = prefetch_factor is not None or num_workers is not None
        if is_async:
            iteration = self.to_async(
                num_workers=num_workers or 1,
                prefetch_factor=prefetch_factor or 1,
                poll_interval=poll_interval,
                in_order=in_order,
                shm_size=shm_size,
            )
        else:
            iteration = self

        return DataLoader(
            iteration,
            num_workers=0,
            timeout=timeout,
            collate_fn=noop_collate_fn,
            pin_memory=pin_memory,
            pin_memory_device=pin_memory_device,
            in_order=in_order,
        )

    def to_async(
        self,
        num_workers: int = 1,
        prefetch_factor: int = 1,
        poll_interval: float = 0.1,
        in_order: bool = True,
        shm_size: int = 4 * 1024**2,
    ):
        return AsyncLavenderDataLoader(
            self,
            num_workers,
            prefetch_factor,
            poll_interval,
            in_order,
            shm_size,
        )

    def complete(self, index: int):
        self._api.complete_index(self._iteration_id, index)

    def pushback(self):
        self._api.pushback(self._iteration_id)

    def __len__(self):
        return self._total

    def _keep_complete_indices(self):
        max_workers = 16
        futures = []
        executor = ThreadPoolExecutor(max_workers=max_workers)

        while not self._stopped:
            if len(self._completed_indices) == 0:
                time.sleep(0.1)
                continue

            index = self._completed_indices.pop()
            try:
                futures.append(executor.submit(self.complete, index))
            except Exception as e:
                warnings.warn(f"Failed to complete index {index}: {e}")

            while len(futures) > max_workers:
                future = next(as_completed(futures))
                futures.remove(future)
                try:
                    future.result()
                except Exception as e:
                    warnings.warn(f"Failed to complete index {index}: {e}")

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                warnings.warn(f"Failed to complete index {index}: {e}")

        executor.shutdown()

    def _mark_completed(self):
        self._completed_indices.update(self._using_indices)
        self._using_indices = set()

    def _mark_using(self, indices: Union[list[int], int]):
        if isinstance(indices, list):
            self._using_indices = set(indices)
        else:
            self._using_indices = {indices}

    def _get_next_item(self):
        try:
            serialized, _ = self._api.get_next_item(
                iteration_id=self._iteration_id,
                rank=self._rank,
                no_cache=self._no_cache,
                max_retry_count=self._max_retry_count,
            )
            self._bytes += len(serialized)
            return deserialize_sample(serialized)
        except LavenderDataApiError as e:
            if "No more indices to pop" in str(e):
                raise StopIteration
            else:
                raise e
        except DeserializeException as e:
            raise ValueError(f"Failed to deserialize sample: {e}")

    def _start(self):
        if self._started:
            return

        self._started = True
        self._complete_thread = threading.Thread(
            target=self._keep_complete_indices, daemon=True
        )
        self._complete_thread.start()

    def _stop(self):
        if self._stopped:
            return

        self._stopped = True
        if self._complete_thread is not None:
            self._complete_thread.join()

    def __next__(self):
        if not self._started:
            self._start()

        self._mark_completed()

        while True:
            try:
                sample_or_batch = self._get_next_item()
                break
            except StopIteration:
                self._stop()
                raise
            except LavenderDataSampleProcessingError as e:
                if self._skip_on_failure:
                    continue
                else:
                    self._stop()
                    raise e

        self._mark_using(sample_or_batch.pop("_lavender_data_indices"))
        return sample_or_batch

    def __iter__(self):
        return self

    def __del__(self):
        self._stop()

    def __getitem__(self, index: int):
        return next(self)


class _ExceptionFromWorker(Exception):
    def __init__(self, exception: str):
        self.exception = exception

    def __str__(self):
        return self.exception

    def __repr__(self):
        return self.exception


def _format_exception(e: Exception):
    return (
        "".join(traceback.format_exception(type(e), e, e.__traceback__))
        + "\n"
        + "".join(traceback.format_tb(e.__traceback__))
    )


EOF_SIGNATURE = b"EOF"
SAMPLE_USED = 1
SAMPLE_NEW = 0


def _int_to_bytes(i: int):
    return i.to_bytes(length=8, byteorder="big", signed=False)


def _bytes_to_int(b: bytes):
    return int.from_bytes(b, byteorder="big", signed=False)


def _fetch_worker(
    iteration_id: str,
    rank: int,
    no_cache: bool,
    max_retry_count: int,
    api_url: Optional[str],
    api_key: Optional[str],
    poll_interval: float,
    shm_size: int,
    stopped_event,
    shm_names,
    error_queue,
):
    _stop_local = False

    def _watch_stopped():
        nonlocal _stop_local
        while not stopped_event.is_set() and not _stop_local:
            time.sleep(poll_interval)
        _stop_local = True

    _watch_stopped_thread = threading.Thread(target=_watch_stopped, daemon=True)
    _watch_stopped_thread.start()

    shms = {}
    for shm_name in shm_names:
        try:
            shms[shm_name] = mp_shared_memory.SharedMemory(
                name=shm_name, create=True, size=shm_size
            )
        except FileExistsError:
            mp_shared_memory.SharedMemory(name=shm_name).unlink()
            shms[shm_name] = mp_shared_memory.SharedMemory(
                name=shm_name, create=True, size=shm_size
            )
        shms[shm_name].buf[0:8] = _int_to_bytes(SAMPLE_USED)

    api = _api(api_url, api_key)
    with api._get_client() as client:

        def _fetch_one():
            try:
                cache_key = api.submit_next_item(
                    iteration_id=iteration_id,
                    rank=rank,
                    no_cache=no_cache,
                    max_retry_count=max_retry_count,
                    client=client,
                ).cache_key
            except LavenderDataApiError as e:
                if "No more indices to pop" in str(e):
                    raise StopIteration
                else:
                    raise e

            current = None
            serialized = None
            error = None
            while (serialized is None and error is None) and not _stop_local:
                time.sleep(poll_interval)

                try:
                    serialized, current = api.get_submitted_result(
                        iteration_id=iteration_id,
                        cache_key=cache_key,
                        client=client,
                    )
                except LavenderDataSampleProcessingError as e:
                    current = e.current
                    error = (current, e.msg)
                except LavenderDataApiError as e:
                    if "Data is still being processed" in str(e):
                        continue
                    elif "Cache key not found" in str(e):
                        raise ValueError("Cache key not found")
                    elif "No more indices to pop" in str(e):
                        raise StopIteration
                    else:
                        raise e

            return current, serialized, error

        shm_idx = 0
        while not _stop_local:
            try:
                while not _stop_local:
                    shm = shms[shm_names[shm_idx]]
                    shm_idx = (shm_idx + 1) % len(shm_names)
                    if _bytes_to_int(shm.buf[0:8].tobytes()) == SAMPLE_NEW:
                        continue
                    break

                fetched = _fetch_one()
                current, serialized, error = fetched

                if serialized is not None:
                    serialized = (
                        _int_to_bytes(0)
                        + _int_to_bytes(current)
                        + _int_to_bytes(len(serialized))
                        + serialized
                        + EOF_SIGNATURE
                    )

                    try:
                        shm.buf[: len(serialized)] = serialized
                    except ValueError as e:
                        if "memoryview assignment" in str(e):
                            error_queue.put(
                                (
                                    -1,
                                    f"shm_size is too small ({shm_size} bytes, {len(serialized)} bytes requested). Please increase it.",
                                )
                            )
                            break
                        else:
                            raise e

                if error is not None:
                    error_queue.put(error)
            except StopIteration:
                _stop_local = True
                break
            except Exception as e:
                error_queue.put((-1, _format_exception(e)))
            except KeyboardInterrupt as e:
                break

    _watch_stopped_thread.join()
    exit(0)


class AsyncLavenderDataLoader:
    def __init__(
        self,
        dl: LavenderDataLoader,
        num_workers: int = 1,
        prefetch_factor: int = 1,
        poll_interval: float = 0.1,
        in_order: bool = True,
        shm_size: int = 4 * 1024**2,
    ):
        if num_workers < 1:
            raise ValueError("num_workers must be greater than 0")

        if prefetch_factor < 1:
            raise ValueError("prefetch_factor must be greater than 0")

        if shm_size < 4 * 1024:
            raise ValueError("shm_size must be greater than 4KB")

        self._dl = dl
        self._num_workers = num_workers
        self._prefetch_factor = prefetch_factor
        self._poll_interval = poll_interval
        self._poll_poll_inerval = poll_interval / 10
        self._in_order = in_order
        self._shm_size = shm_size

        self._mp_ctx = mp.get_context("spawn")
        self._stopped_event = self._mp_ctx.Event()
        self._stopped_local = False
        self._started = False
        self._shm_names = {
            i: [
                f"shm-{i}-{j}-{secrets.token_hex(4)}"
                for j in range(self._prefetch_factor)
            ]
            for i in range(self._num_workers)
        }
        self._error_queue = self._mp_ctx.Queue()
        self._fetch_processes: list[mp.Process] = []
        self._joined_fetch_processes = 0

        self._current = 0
        self._error: Optional[Exception] = None
        self._arrived: dict[int, dict] = {}

        self._using_shm_names: set[str] = set()
        self._used_shm_names: set[str] = set()

        self._watch_data_threads: list[threading.Thread] = []
        self._watch_used_shm_thread: Optional[threading.Thread] = None
        self._watch_error_queue_thread: Optional[threading.Thread] = None
        self._watch_processes_thread: Optional[threading.Thread] = None
        self._watch_stopped_thread: Optional[threading.Thread] = None

    def _start(self):
        if self._started:
            return

        self._started = True
        self._dl._start()
        self._start_fetch_processes()

    def _watch_data(self, shm_name: str):
        try:
            while True:
                try:
                    shm = mp_shared_memory.SharedMemory(name=shm_name)
                    break
                except (FileNotFoundError, ValueError):
                    continue

            while not self._stopped_local:
                if _bytes_to_int(shm.buf[0:8].tobytes()) == SAMPLE_USED:
                    time.sleep(self._poll_poll_inerval)
                    continue

                current = _bytes_to_int(shm.buf[8:16].tobytes())
                length = _bytes_to_int(shm.buf[16:24].tobytes())
                if (
                    shm.buf[length + 24 : length + 24 + len(EOF_SIGNATURE)].tobytes()
                    != EOF_SIGNATURE
                ):
                    continue

                try:
                    data = deserialize_sample(shm.buf[24 : length + 24])
                    self._arrived[current] = (shm_name, data)
                except DeserializeException as e:
                    self._error_queue.put((-1, _format_exception(e)))
        except Exception as e:
            self._error_queue.put((-1, _format_exception(e)))

    def _watch_used_shm(self):
        try:
            _shm = {}
            for shm_names in self._shm_names.values():
                for shm_name in shm_names:
                    while True:
                        try:
                            _shm[shm_name] = mp_shared_memory.SharedMemory(
                                name=shm_name
                            )
                            break
                        except (FileNotFoundError, ValueError):
                            continue

            while not self._stopped_local:
                if len(self._used_shm_names) == 0:
                    time.sleep(self._poll_poll_inerval)
                    continue

                shm_name = self._used_shm_names.pop()
                _shm[shm_name].buf[0:8] = _int_to_bytes(SAMPLE_USED)
        except Exception as e:
            self._error_queue.put((-1, _format_exception(e)))

    def _watch_error_queue(self):
        while not self._stopped_local:
            try:
                failed_index, error = self._error_queue.get(timeout=0.1)
                if failed_index == -1 or not self._dl._skip_on_failure:
                    # fatal
                    self._error = _ExceptionFromWorker(error)
                    self._stopped_event.set()
                else:
                    self._arrived[failed_index] = (None, None)
            except queue.Empty:
                pass

    def _watch_processes(self):
        while self._joined_fetch_processes < len(self._fetch_processes):
            for process in self._fetch_processes:
                if process.exitcode is not None:
                    self._joined_fetch_processes += 1

        self._stopped_event.set()

    def _watch_stopped(self):
        self._stopped_event.wait()
        self._stopped_local = True

        for thread in self._watch_data_threads:
            thread.join()

        if self._watch_used_shm_thread is not None:
            self._watch_used_shm_thread.join()

        if self._watch_error_queue_thread is not None:
            self._watch_error_queue_thread.join()

        if self._watch_processes_thread is not None:
            self._watch_processes_thread.join()

        for shm_names in self._shm_names.values():
            for shm_name in shm_names:
                try:
                    shm = mp_shared_memory.SharedMemory(name=shm_name)
                    shm.unlink()
                except FileNotFoundError:
                    continue
        self._error_queue.close()
        for process in self._fetch_processes:
            process.join()
        self._dl._stop()

    def _wait_cleanup(self):
        while not self._dl._stopped:
            time.sleep(0.1)

    def _start_fetch_processes(self):
        for shm_names in self._shm_names.values():
            for shm_name in shm_names:
                _thread = threading.Thread(
                    target=self._watch_data,
                    args=(shm_name,),
                    daemon=True,
                )
                _thread.start()
                self._watch_data_threads.append(_thread)
        self._watch_used_shm_thread = threading.Thread(
            target=self._watch_used_shm, daemon=True
        )
        self._watch_used_shm_thread.start()
        self._watch_error_queue_thread = threading.Thread(
            target=self._watch_error_queue, daemon=True
        )
        self._watch_error_queue_thread.start()
        self._watch_stopped_thread = threading.Thread(
            target=self._watch_stopped, daemon=True
        )
        self._watch_stopped_thread.start()

        for i in range(self._num_workers):
            process = self._mp_ctx.Process(
                target=_fetch_worker,
                args=(
                    self._dl._iteration_id,
                    self._dl._rank,
                    self._dl._no_cache,
                    self._dl._max_retry_count,
                    self._dl._api.api_url,
                    self._dl._api.api_key,
                    self._poll_interval,
                    self._shm_size,
                    self._stopped_event,
                    self._shm_names[i],
                    self._error_queue,
                ),
            )
            process.start()
            self._fetch_processes.append(process)

        self._watch_processes_thread = threading.Thread(
            target=self._watch_processes, daemon=True
        )
        self._watch_processes_thread.start()

    def _mark_shm_using(self, shm_name: str):
        self._using_shm_names.add(shm_name)

    def _mark_shm_used(self):
        self._used_shm_names.update(self._using_shm_names)
        self._using_shm_names = set()

    def __len__(self):
        return len(self._dl)

    def __next__(self):
        if not self._started:
            self._start()

        self._mark_shm_used()
        self._dl._mark_completed()

        shm_name = None
        data = None
        while data is None or shm_name is None:
            if self._joined_fetch_processes == len(self._fetch_processes):
                raise self._error or StopIteration

            if self._stopped_local:
                raise self._error or StopIteration

            try:
                if self._in_order:
                    shm_name, data = self._arrived.pop(self._current)
                else:
                    shm_name, data = self._arrived.pop(list(self._arrived.keys())[0])
            except (KeyError, IndexError):
                time.sleep(self._poll_poll_inerval)
                continue

            self._current += 1

        self._mark_shm_using(shm_name)
        self._dl._mark_using(data.pop("_lavender_data_indices"))
        return data

    def __iter__(self):
        try:
            while True:
                yield next(self)
        except StopIteration:
            pass
        finally:
            self._stopped_event.set()
            self._wait_cleanup()

    def __getitem__(self, index: int):
        return next(self)
