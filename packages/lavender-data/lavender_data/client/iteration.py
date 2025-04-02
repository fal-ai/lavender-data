from typing import Optional
from concurrent.futures import ThreadPoolExecutor, Future, as_completed

from lavender_data.logging import get_logger
from lavender_data.client.api import (
    complete_index,
    create_iteration,
    get_iterations,
    get_iteration,
    get_next_item,
    get_dataset,
    GetIterationResponse,
    LavenderDataApiError,
    IterationFilter,
    IterationPreprocessor,
    IterationCollater,
)

__all__ = ["Iteration"]


def noop_collate_fn(x):
    return x[0]


class Iteration:
    def __init__(
        self,
        dataset_id: str,
        iteration_id: str,
        total: int,
    ):
        self._dataset_id = dataset_id
        self._iteration_id = iteration_id
        self._total = total

        self.last_indices = None

    @classmethod
    def from_dataset(
        cls,
        dataset_id: Optional[str] = None,
        dataset_name: Optional[str] = None,
        shardsets: Optional[list[str]] = None,
        filters: Optional[list[tuple[str, dict]]] = None,
        preprocessors: Optional[list[tuple[str, dict]]] = None,
        collater: Optional[tuple[str, dict]] = None,
        shuffle: Optional[bool] = None,
        shuffle_seed: Optional[int] = None,
        shuffle_block_size: Optional[int] = None,
        batch_size: Optional[int] = None,
        replication_pg: Optional[list[list[int]]] = None,
        resume: Optional[bool] = False,
    ):
        if dataset_id is None and dataset_name is None:
            raise ValueError("Either dataset_id or dataset_name must be provided")

        if dataset_id is not None and dataset_name is not None:
            raise ValueError("Only one of dataset_id or dataset_name can be provided")

        if dataset_id is None:
            dataset_id = get_dataset(name=dataset_name).id

        logger = get_logger(__name__)
        if resume:
            try:
                return cls.from_latest_iteration(
                    dataset_id=dataset_id, dataset_name=dataset_name
                )
            except ValueError as e:
                if "No iterations exist" in str(e):
                    logger.warning("No iterations exist, creating a new one")
                else:
                    raise e

        iteration = create_iteration(
            dataset_id=dataset_id,
            shardsets=shardsets,
            filters=(
                [
                    IterationFilter.from_dict({"name": name, "params": params})
                    for name, params in filters
                ]
                if filters is not None
                else None
            ),
            preprocessors=(
                [
                    IterationPreprocessor.from_dict({"name": name, "params": params})
                    for name, params in preprocessors
                ]
                if preprocessors is not None
                else None
            ),
            collater=(
                IterationCollater.from_dict(
                    {"name": collater[0], "params": collater[1]}
                )
                if collater is not None
                else None
            ),
            shuffle=shuffle,
            shuffle_seed=shuffle_seed,
            shuffle_block_size=shuffle_block_size,
            batch_size=batch_size,
            replication_pg=replication_pg,
        )
        return cls.from_iteration(iteration)

    @classmethod
    def from_latest_iteration(
        cls, dataset_id: Optional[str] = None, dataset_name: Optional[str] = None
    ):
        iterations = get_iterations(dataset_id=dataset_id, dataset_name=dataset_name)
        if len(iterations) == 0:
            raise ValueError("No iterations exist")
        return cls.from_iteration(iterations[0])

    @classmethod
    def from_iteration_id(cls, iteration_id: str):
        iteration = get_iteration(iteration_id)
        return cls.from_iteration(iteration)

    @classmethod
    def from_iteration(cls, iteration: GetIterationResponse):
        return cls(
            dataset_id=iteration.dataset_id,
            iteration_id=iteration.id,
            total=iteration.total,
        )

    def to_torch_dataloader(
        self,
        pin_memory: bool = False,
        timeout: float = 0,
        multiprocessing_context=None,
        *,
        num_workers: int = 0,
        prefetch_factor: Optional[int] = None,
        persistent_workers: bool = False,
        pin_memory_device: str = "",
    ):
        try:
            from torch.utils.data import DataLoader
        except ImportError:
            raise ImportError("torch is not installed. Please install it first.")

        is_async = prefetch_factor is not None
        num_workers = max(1, num_workers)
        return DataLoader(
            (
                self
                if not is_async
                else AsyncIteration(self, num_workers, prefetch_factor)
            ),
            num_workers=1 if is_async else 0,
            timeout=timeout,
            collate_fn=noop_collate_fn,
            multiprocessing_context=multiprocessing_context,
            prefetch_factor=prefetch_factor,
            persistent_workers=persistent_workers,
            pin_memory=pin_memory,
            pin_memory_device=pin_memory_device,
            in_order=True,
        )

    def complete(self, index: int):
        complete_index(self._iteration_id, index)

    def __len__(self):
        return self._total

    def __next__(self):
        if self.last_indices is not None:
            for index in self.last_indices:
                # TODO handle prefetch
                self.complete(index)
            self.last_indices = None

        try:
            sample_or_batch = get_next_item(iteration_id=self._iteration_id, rank=0)
            indices = sample_or_batch["_lavender_data_indices"]
            if isinstance(indices, list):
                self.last_indices = indices
            else:
                self.last_indices = [indices]
        except LavenderDataApiError as e:
            if "No more indices to pop" in str(e):
                raise StopIteration
            else:
                raise e
        return sample_or_batch

    def __iter__(self):
        return self


class AsyncIteration:
    def __init__(self, iteration: Iteration, num_workers: int, prefetch_factor: int):
        self.iteration = iteration
        self.num_workers = num_workers
        self.prefetch_factor = prefetch_factor
        self.executor: Optional[ThreadPoolExecutor] = None  # to be serializable
        self.futures: list[Future] = []
        self.arrived: list[tuple[int, dict]] = []
        self.current = 0
        self.stopped = False

    def _submit_next(self):
        if self.stopped:
            return

        queue_size = self.num_workers * self.prefetch_factor
        if self.executor is None:
            self.executor = ThreadPoolExecutor(queue_size)

        while len(self.futures) < queue_size:
            future = self.executor.submit(self.iteration.__next__)
            self.futures.append(future)

    def __len__(self):
        return len(self.iteration)

    def __next__(self):
        if len(self.futures) == 0:
            self._submit_next()

        next_index = self.current + 1

        # check if the data has already arrived during the previous iteration
        already_arrived = [data for i, data in self.arrived if i == next_index]
        if len(already_arrived) > 0:
            self.current = next_index
            return already_arrived[0]

        # if the iteration is stopped and there are no more futures to be waited, stop iteration
        if self.stopped and len(self.futures) == 0:
            raise StopIteration

        while True:
            try:
                # wait for the data to arrive
                future = next(as_completed(self.futures))
                self.futures.remove(future)
                data = future.result()
            except StopIteration:
                # it means one of the workers detected that the iteration is stopped
                # but it's not guaranteed that all data from the other workers has returned
                self.stopped = True

            self._submit_next()

            arrived_index = data["_lavender_data_current"]

            if arrived_index == next_index:
                # if arrived index is the next index, return the data
                self.current = next_index
                break
            else:
                # if arrived index is not the next index, add the data to the list
                self.arrived.append((arrived_index, data))

        return data

    def __iter__(self):
        return self

    def __getitem__(self, index: int):
        return next(self)
