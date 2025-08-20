import time
import threading
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        cluster_sync: Optional[bool] = None,
        no_cache: Optional[bool] = None,
        num_workers: Optional[int] = None,
        prefetch_factor: Optional[int] = None,
        in_order: Optional[bool] = None,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self._bytes = 0
        self._started = False
        self._stopped = False

        self._current = -1
        self._stop_completed_thread = False
        self._complete_thread: Optional[threading.Thread] = None

        self._using_indices = set()
        self._completed_indices = set()
        self._no_cache = no_cache
        self._max_retry_count = max_retry_count
        self._skip_on_failure = skip_on_failure
        self._rank = rank

        self._api_url = api_url
        self._api_key = api_key
        self._api = _api(self._api_url, self._api_key)

        if iteration_id is None:
            if dataset_id is None:
                if dataset_name is None:
                    raise ValueError(
                        "Either dataset_id or dataset_name must be provided"
                    )
                dataset_id = self._api.get_dataset(name=dataset_name).id

            iteration_response = self._api.create_iteration(
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
                no_cache=no_cache,
                num_workers=num_workers,
                prefetch_factor=prefetch_factor,
                in_order=in_order,
            )
        else:
            iteration_response = self._api.get_iteration(iteration_id)

        self._dataset_id = iteration_response.dataset_id
        self._iteration_id = iteration_response.id
        self._total = iteration_response.total

    def torch(self, *args, **kwargs):
        try:
            from torch.utils.data import DataLoader
        except ImportError:
            raise ImportError("torch is not installed. Please install it first.")

        self._total += 1
        return DataLoader(self, *args, **kwargs)

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

        while not self._stop_completed_thread:
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
        serialized = None
        with self._api._get_client() as client:
            while serialized is None and not self._stopped:
                try:
                    serialized, self._current = self._api.get_next_item(
                        iteration_id=self._iteration_id,
                        rank=self._rank,
                        client=client,
                    )
                except LavenderDataSampleProcessingError as e:
                    self._current = e.current
                    raise e
                except LavenderDataApiError as e:
                    if "Data is still being processed" in str(e):
                        continue
                    elif "No more indices to pop" in str(e):
                        raise StopIteration
                    else:
                        raise e
        self._bytes += len(serialized)
        try:
            return deserialize_sample(serialized)
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

        if self._complete_thread is not None:
            self._stop_completed_thread = True
            self._complete_thread.join()
            self._complete_thread = None

        self._stopped = True

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

    def __getitem__(self, index: int):
        return next(self)
