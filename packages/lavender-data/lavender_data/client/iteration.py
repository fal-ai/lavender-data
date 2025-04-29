import time
from typing import Optional, Union, Literal
from concurrent.futures import ThreadPoolExecutor, Future, as_completed

from lavender_data.client.api import (
    get_client,
    LavenderDataClient,
    LavenderDataApiError,
    IterationFilter,
    IterationPreprocessor,
    IterationCollater,
)

__all__ = ["LavenderDataLoader"]


def noop_collate_fn(x):
    return x[0]


def _parse_registry_params(
    registry_name: Literal["filter", "preprocessor", "collater"],
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
    elif registry_name == "preprocessor":
        return IterationPreprocessor.from_dict(d)
    elif registry_name == "collater":
        return IterationCollater.from_dict(d)
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
        preprocessors: Optional[list[Union[tuple[str, dict], str]]] = None,
        collater: Optional[Union[tuple[str, dict], str]] = None,
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
                preprocessors=(
                    [_parse_registry_params("preprocessor", f) for f in preprocessors]
                    if preprocessors is not None
                    else None
                ),
                collater=(
                    _parse_registry_params("collater", collater)
                    if collater is not None
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

        self._last_indices = None
        self._no_cache = no_cache
        self._rank = rank

        self.id = self._iteration_id

        self.api_url = api_url
        self.api_key = api_key

    def _api(self):
        return _api(self.api_url, self.api_key)

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
        self._api().complete_index(self._iteration_id, index)

    def pushback(self):
        self._api().pushback(self._iteration_id)

    def __len__(self):
        return self._total

    def _complete_last_indices(self):
        if self._last_indices is not None:
            for index in self._last_indices:
                self.complete(index)
            self._last_indices = None

    def _set_last_indices(self, sample_or_batch):
        indices = sample_or_batch["_lavender_data_indices"]
        if isinstance(indices, list):
            self._last_indices = indices
        else:
            self._last_indices = [indices]

    def _get_next_item(self):
        try:
            sample_or_batch = self._api().get_next_item(
                iteration_id=self._iteration_id,
                rank=self._rank,
                no_cache=self._no_cache,
            )
        except LavenderDataApiError as e:
            if "No more indices to pop" in str(e):
                raise StopIteration
            else:
                raise e

        return sample_or_batch

    def _submit_next_item(self) -> str:
        cache_key = (
            self._api()
            .submit_next_item(
                iteration_id=self._iteration_id,
                rank=self._rank,
                no_cache=self._no_cache,
            )
            .cache_key
        )
        return cache_key

    def _get_submitted_result(self, cache_key: str):
        try:
            return self._api().get_submitted_result(
                iteration_id=self._iteration_id,
                cache_key=cache_key,
            )
        except LavenderDataApiError as e:
            if "Data is still being processed" in str(e):
                return None
            elif "Cache key not found" in str(e):
                raise ValueError("Cache key not found")
            elif "No more indices to pop" in str(e):
                raise StopIteration
            else:
                raise e

    def __next__(self):
        self._complete_last_indices()
        sample_or_batch = self._get_next_item()
        self._set_last_indices(sample_or_batch)
        return sample_or_batch

    def __iter__(self):
        return self

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

        self.dl = dl
        self.prefetch_factor = prefetch_factor
        self.poll_interval = poll_interval
        self.in_order = in_order
        self.executor: Optional[ThreadPoolExecutor] = None  # to be serializable
        self.futures: list[Future] = []
        self.arrived: list[tuple[int, dict]] = []
        self.current = 0
        self.stopped = False

    def _get_submitted_result(self, cache_key: str):
        while True:
            data = self.dl._get_submitted_result(cache_key)
            if data is not None:
                return data
            else:
                time.sleep(self.poll_interval)

    def _submit_next(self):
        if self.stopped:
            return

        queue_size = self.prefetch_factor
        if self.executor is None:
            self.executor = ThreadPoolExecutor(queue_size)

        while len(self.futures) < queue_size:
            try:
                cache_key = self.dl._submit_next_item()
            except LavenderDataApiError as e:
                if "No more indices to pop" in str(e):
                    self.stopped = True
                    return
                else:
                    raise e
            future = self.executor.submit(
                self._get_submitted_result, cache_key=cache_key
            )
            self.futures.append(future)

    def __len__(self):
        return len(self.dl)

    def __next__(self):
        if len(self.futures) == 0:
            self._submit_next()

        self.dl._complete_last_indices()
        next_index = self.current + 1
        # check if the data has already arrived during the previous iteration
        already_arrived = (
            [data for i, data in self.arrived if i == next_index]
            if self.in_order
            else self.arrived
        )
        if len(already_arrived) > 0:
            data = already_arrived[0]
            self.current = next_index
            self.arrived = [a for a in self.arrived if a[0] != next_index]
            self.dl._set_last_indices(data)
            return data

        # if the iteration is stopped and there are no more futures to be waited, stop iteration
        while True:
            if self.stopped and len(self.futures) == 0:
                raise StopIteration

            data = None
            try:
                # wait for the data to arrive
                future = next(as_completed(self.futures))
                self.futures.remove(future)
                data = future.result()
            except StopIteration:
                # it means one of the workers detected that the iteration is stopped
                # but it's not guaranteed that all data from the other workers has returned
                self.stopped = True
                continue

            self._submit_next()

            arrived_index = data["_lavender_data_current"]

            if not self.in_order or arrived_index == next_index:
                # if arrived index is the next index, return the data
                self.current = next_index
                self.dl._set_last_indices(data)
                break
            else:
                # if arrived index is not the next index, add the data to the list
                self.arrived.append((arrived_index, data))

        return data

    def __iter__(self):
        return self

    def __getitem__(self, index: int):
        return next(self)
