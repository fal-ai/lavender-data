import time
import threading
import warnings
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

        self._last_indices = set()
        self._completed_indices = set()
        self._no_cache = no_cache
        self._max_retry_count = max_retry_count
        self._skip_on_failure = skip_on_failure
        self._rank = rank

        self._api_url = api_url
        self._api_key = api_key
        self._api = _api(self._api_url, self._api_key)

        self._bytes = 0
        self._stopped = False

        self.id = self._iteration_id

        self._complete_thread = threading.Thread(
            target=self._keep_complete_indices, daemon=True
        )
        self._complete_thread.start()

    def torch(
        self,
        pin_memory: bool = False,
        timeout: float = 0,
        multiprocessing_context=None,
        *,
        prefetch_factor: Optional[int] = None,
        persistent_workers: bool = False,
        pin_memory_device: str = "",
        in_order: bool = True,
        poll_interval: float = 0.01,
    ):
        try:
            from torch.utils.data import DataLoader
        except ImportError:
            raise ImportError("torch is not installed. Please install it first.")

        is_async = prefetch_factor is not None
        if is_async:
            iteration = self.to_async(prefetch_factor, poll_interval, in_order)
        else:
            iteration = self

        return DataLoader(
            iteration,
            num_workers=1 if is_async else 0,
            timeout=timeout,
            collate_fn=noop_collate_fn,
            multiprocessing_context=multiprocessing_context,
            prefetch_factor=prefetch_factor,
            persistent_workers=persistent_workers,
            pin_memory=pin_memory,
            pin_memory_device=pin_memory_device,
            in_order=in_order,
        )

    def to_async(
        self,
        prefetch_factor: int,
        poll_interval: float = 0.1,
        in_order: bool = True,
    ):
        return AsyncLavenderDataLoader(
            self,
            prefetch_factor,
            poll_interval,
            in_order,
        )

    def complete(self, index: int):
        self._api.complete_index(self._iteration_id, index)

    def pushback(self):
        self._api.pushback(self._iteration_id)

    def __len__(self):
        return self._total

    def _keep_complete_indices(self):
        while not self._stopped:
            if len(self._completed_indices) == 0:
                time.sleep(0.1)
                continue

            index = self._completed_indices.pop()
            self.complete(index)

    def _complete_last_indices(self):
        self._completed_indices.update(self._last_indices)
        self._last_indices = set()

    def _set_last_indices(self, sample_or_batch):
        indices = sample_or_batch["_lavender_data_indices"]
        if isinstance(indices, list):
            self._last_indices = set(indices)
        else:
            self._last_indices = {indices}

    def _get_next_item(self):
        try:
            serialized = self._api.get_next_item(
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

    def _submit_next_item(self) -> str:
        cache_key = self._api.submit_next_item(
            iteration_id=self._iteration_id,
            rank=self._rank,
            no_cache=self._no_cache,
            max_retry_count=self._max_retry_count,
        ).cache_key
        return cache_key

    def _get_submitted_result(self, cache_key: str):
        try:
            serialized = self._api.get_submitted_result(
                iteration_id=self._iteration_id,
                cache_key=cache_key,
            )
            self._bytes += len(serialized)
            return deserialize_sample(serialized)
        except LavenderDataApiError as e:
            if "Data is still being processed" in str(e):
                return None
            elif "Cache key not found" in str(e):
                raise ValueError("Cache key not found")
            elif "No more indices to pop" in str(e):
                raise StopIteration
            else:
                raise e
        except DeserializeException as e:
            raise ValueError(f"Failed to deserialize sample: {e}")

    def _stop(self):
        self._stopped = True
        self._complete_thread.join()

    def __next__(self):
        self._complete_last_indices()

        while True:
            try:
                sample_or_batch = self._get_next_item()
                break
            except LavenderDataSampleProcessingError as e:
                if self._skip_on_failure:
                    continue
                else:
                    raise e

        self._set_last_indices(sample_or_batch)
        return sample_or_batch

    def __iter__(self):
        try:
            while True:
                yield next(self)
        except StopIteration:
            pass
        finally:
            self._stop()

    def __getitem__(self, index: int):
        return next(self)


class AsyncLavenderDataLoader:
    def __init__(
        self,
        dl: LavenderDataLoader,
        prefetch_factor: int,
        poll_interval: float = 0.1,
        in_order: bool = True,
    ):
        if prefetch_factor < 1:
            raise ValueError("prefetch_factor must be greater than 0")

        self._dl = dl
        self._prefetch_factor = prefetch_factor
        self._poll_interval = poll_interval
        self._in_order = in_order
        self._arrived: list[tuple[int, dict]] = []
        self._current = 0
        self._stopped = False
        self._fetch_threads: list[threading.Thread] = []
        self._joined_fetch_threads = 0
        self._error: Optional[Exception] = None

    def _stop(self):
        self._stopped = True
        for thread in self._fetch_threads:
            thread.join()
        self._dl._stop()

    def _get_submitted_result(self, cache_key: str):
        while True:
            data = self._dl._get_submitted_result(cache_key)
            if data is not None:
                return data
            else:
                time.sleep(self._poll_interval)

    def _fetch_one(self):
        try:
            cache_key = self._dl._submit_next_item()
        except LavenderDataApiError as e:
            if "No more indices to pop" in str(e):
                raise StopIteration
            else:
                raise e

        data = None
        arrived_index = None
        while arrived_index is None and not self._stopped:
            time.sleep(self._poll_interval)

            try:
                data = self._dl._get_submitted_result(cache_key)
                if data is not None:
                    arrived_index = data["_lavender_data_current"]
            except LavenderDataSampleProcessingError as e:
                if self._dl._skip_on_failure:
                    arrived_index = e.current
                else:
                    raise e

        return arrived_index, data

    def _keep_fetching(self):
        while not self._stopped:
            try:
                fetched = self._fetch_one()
                arrived_index, data = fetched
                self._arrived.append((arrived_index, data))
            except StopIteration:
                break
            except Exception as e:
                self._error = e
                self._stopped = True

        self._joined_fetch_threads += 1

    def _start_fetch_threads(self):
        for _ in range(self._prefetch_factor):
            thread = threading.Thread(target=self._keep_fetching)
            thread.start()
            self._fetch_threads.append(thread)

    def __len__(self):
        return len(self._dl)

    def __next__(self):
        if len(self._fetch_threads) == 0:
            self._start_fetch_threads()

        self._dl._complete_last_indices()

        data = None
        while data is None:
            if self._stopped:
                raise self._error or StopIteration

            if self._joined_fetch_threads == len(self._fetch_threads):
                raise StopIteration

            arrived = next(
                (
                    (i, data)
                    for i, data in self._arrived
                    if i == self._current or not self._in_order
                ),
                None,
            )

            if arrived is None:
                continue

            arrived_index, data = arrived
            self._arrived = [a for a in self._arrived if a[0] != arrived_index]
            self._current += 1

        self._dl._set_last_indices(data)
        return data

    def __iter__(self):
        try:
            while True:
                yield next(self)
        except StopIteration:
            pass
        finally:
            self._stop()

    def __getitem__(self, index: int):
        return next(self)
