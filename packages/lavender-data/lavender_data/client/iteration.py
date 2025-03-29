from typing import Optional

from lavender_data.logging import get_logger
from lavender_data.client.api import (
    complete_index,
    create_iteration,
    get_iterations,
    get_iteration,
    get_next_item,
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
        dataset_id: str,
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
        logger = get_logger(__name__)
        if resume:
            try:
                return cls.from_latest_iteration(dataset_id)
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
    def from_latest_iteration(cls, dataset_id: str):
        iterations = get_iterations(dataset_id=dataset_id)
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
        prefetch_factor: Optional[int] = None,
        persistent_workers: bool = False,
        pin_memory_device: str = "",
    ):
        try:
            from torch.utils.data import DataLoader
        except ImportError:
            raise ImportError("torch is not installed. Please install it first.")

        return DataLoader(
            self,
            num_workers=1 if prefetch_factor is not None else 0,
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

    def __getitem__(self, index: int):
        return next(self)
