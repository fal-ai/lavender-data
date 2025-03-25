import os
from typing import Optional

from pydantic import BaseModel

from lavender_data.client.api import (
    complete_index,
    create_iteration,
    get_iterations,
    get_iteration,
    get_next_item,
    GetIterationResponse,
    LavenderDataApiError,
)

__all__ = ["Iteration"]


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
        resume: Optional[bool] = False,
        shardsets: Optional[list[str]] = None,
        filter: Optional[str] = None,
        preprocessor: Optional[str] = None,
        collater: Optional[str] = None,
        shuffle: Optional[bool] = None,
        shuffle_seed: Optional[int] = None,
        shuffle_block_size: Optional[int] = None,
        batch_size: Optional[int] = None,
        replication_pg: Optional[list[list[int]]] = None,
    ):
        if resume:
            return cls.from_latest_iteration(dataset_id)
        else:
            iteration = create_iteration(
                dataset_id=dataset_id,
                shardsets=shardsets,
                filter=filter,
                preprocessor=preprocessor,
                collater=collater,
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

    def complete(self, index: int):
        complete_index(self._iteration_id, index)

    def __len__(self):
        return self._total

    def __next__(self):
        if self.last_indices is not None:
            for index in self.last_indices:
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
