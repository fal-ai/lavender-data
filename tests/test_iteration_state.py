import os
import unittest
import random
import math
from typing import Optional
import numpy as np
import tqdm
from datetime import datetime
from lavender_data.server.cache import get_cache, setup_cache
from lavender_data.server.db.models import (
    Iteration,
    Shardset,
    DatasetColumn,
    Shard,
    Dataset,
)
from lavender_data.server.shardset import span
from lavender_data.server.iteration import (
    IterationState,
    IterationStateException,
)


class TestIterationState(unittest.TestCase):
    def setUp(self):
        # Mock Redis client
        # self.mock_cache = MagicMock()
        setup_cache()
        self.cache = next(get_cache())
        self.assertNotEqual(self.cache, None, "Redis client not found")

        # Setup mock data
        self.num_shards = 100
        self.samples_per_shard = 100
        self.total_samples = self.num_shards * self.samples_per_shard

    def get_iteration(
        self,
        uid: str,
        shuffle: bool = False,
        shuffle_seed: Optional[int] = None,
        shuffle_block_size: Optional[int] = None,
        replication_pg: Optional[list[list[int]]] = None,
    ):
        for key in self.cache.keys(f"test:it-{uid}:*"):
            self.cache.delete(key)

        return Iteration(
            id=f"test:it-{uid}",
            dataset_id=f"test:ds-{uid}",
            total=self.total_samples,
            shuffle=shuffle,
            shuffle_seed=shuffle_seed,
            shuffle_block_size=shuffle_block_size,
            replication_pg=replication_pg,
            batch_size=0,
            worker_endpoint=None,
            dataset=Dataset(
                id=f"test:ds-{uid}",
                uid_column_name="uid",
                columns=[
                    DatasetColumn(
                        id=f"test:dc-{uid}-1",
                        dataset_id=f"test:ds-{uid}",
                        shardset_id=f"test:ss-{uid}-1",
                        name="uid",
                        type="int",
                    ),
                    DatasetColumn(
                        id=f"test:dc-{uid}-2",
                        dataset_id=f"test:ds-{uid}",
                        shardset_id=f"test:ss-{uid}-1",
                        name="test_column",
                        type="int",
                    ),
                ],
            ),
            shardsets=[
                Shardset(
                    id=f"test:ss-{uid}-1",
                    dataset_id=f"test:ds-{uid}",
                    location="test_location_1",
                    shards=[
                        Shard(
                            id=f"test:sd-{uid}-1",
                            shardset_id=f"test:ss-{uid}-1",
                            location="test_location_1",
                            filesize=1000,
                            samples=self.samples_per_shard,
                            index=i,
                            format="int",
                        )
                        for i in range(self.num_shards)
                    ],
                    columns=[
                        DatasetColumn(
                            id=f"test:dc-{uid}-1",
                            dataset_id=f"test:ds-{uid}",
                            shardset_id=f"test:ss-{uid}-1",
                            name="uid",
                            type="int",
                        ),
                        DatasetColumn(
                            id=f"test:dc-{uid}-2",
                            dataset_id=f"test:ds-{uid}",
                            shardset_id=f"test:ss-{uid}-1",
                            name="test_column",
                            type="int",
                        ),
                    ],
                    created_at=datetime.now(),
                ),
            ],
        )

    def test_pop_index_no_shuffle(self):
        # Setup
        rank = 0

        iteration = self.get_iteration("test_pop_index_no_shuffle")

        iteration_state = IterationState(iteration.id, self.cache)
        iteration_state.init(iteration)

        # Verify
        # Should push indices 0-999 in order (no shuffle)
        for expected_index in tqdm.tqdm(
            range(self.total_samples), desc="test_pop_index_no_shuffle"
        ):
            retrieved_index = iteration_state._pop_index(rank)
            self.assertEqual(retrieved_index, expected_index)

    def test_pop_index_shuffle(self):
        # Setup
        rank = 0

        shuffle_seed = 42
        shuffle_block_size = 10

        iteration = self.get_iteration(
            "test_pop_index_shuffle",
            shuffle=True,
            shuffle_seed=shuffle_seed,
            shuffle_block_size=shuffle_block_size,
        )

        iteration_state = IterationState(iteration.id, self.cache)
        iteration_state.init(iteration)

        ordered_indices = list(range(self.total_samples))
        retrieved_indices = [
            iteration_state._pop_index(rank) for _ in range(self.total_samples)
        ]

        # Completeness and Uniqueness
        self.assertEqual(len(set(retrieved_indices)), len(retrieved_indices))
        self.assertEqual(set(retrieved_indices), set(ordered_indices))

        # Evenly shuffled
        expected_avg = self.total_samples // 2
        acceptable_gap = expected_avg * 0.3  # 30%
        bin_size = math.ceil(self.total_samples / shuffle_block_size)
        current_bin = 0
        for i, index in enumerate(retrieved_indices):
            if i % bin_size == 0:
                if i != 0:
                    avg = current_bin / bin_size
                    gap = abs(avg - expected_avg)
                    self.assertLessEqual(gap, acceptable_gap)
                    current_bin = 0
            current_bin += index

    def test_pop_index_no_shuffle_multiple_ranks(self):
        # Setup
        ranks = [0, 1, 2]

        iteration = self.get_iteration("test_pop_index_no_shuffle_multiple_ranks")

        iteration_state = IterationState(iteration.id, self.cache)
        iteration_state.init(iteration)

        ranks_done = {rank: False for rank in ranks}
        retrieved = []
        for i in tqdm.tqdm(
            range(int(self.total_samples * 1.5)),
            desc="test_pop_index_no_shuffle_multiple_ranks",
        ):
            rank = ranks[i % len(ranks)]
            try:
                retrieved_index = iteration_state._pop_index(rank)
            except IterationStateException:
                ranks_done[rank] = True
                if all(ranks_done.values()):
                    break
                continue
            retrieved.append(retrieved_index)

        self.assertEqual(len(set(retrieved)), len(retrieved), "duplicate indices")
        self.assertEqual(set(retrieved), set(range(self.total_samples)))

    def test_pop_index_shuffle_multiple_ranks(self):
        # Setup
        ranks = [0, 1, 2]

        shuffle_seed = random.randint(0, 1000000)
        shuffle_block_size = 10

        iteration = self.get_iteration(
            "test_pop_index_shuffle_multiple_ranks",
            shuffle=True,
            shuffle_seed=shuffle_seed,
            shuffle_block_size=shuffle_block_size,
        )

        iteration_state = IterationState(iteration.id, self.cache)
        iteration_state.init(iteration)

        ranks_done = {rank: False for rank in ranks}
        retrieved = []
        for i in tqdm.tqdm(
            range(int(self.total_samples * 1.5)),
            desc="test_pop_index_shuffle_multiple_ranks",
        ):
            rank = ranks[i % len(ranks)]
            try:
                retrieved_index = iteration_state._pop_index(rank)
            except IterationStateException:
                ranks_done[rank] = True
                if all(ranks_done.values()):
                    break
                continue
            retrieved.append(retrieved_index)

        self.assertEqual(len(set(retrieved)), len(retrieved), "duplicate indices")
        self.assertEqual(set(retrieved), set(range(self.total_samples)))

    def test_next_item(self):
        rank = 0
        iteration = self.get_iteration("test_next_item")

        iteration_state = IterationState(iteration.id, self.cache)
        iteration_state.init(iteration)

        # Verify
        # Should push indices 0-999 in order (no shuffle)
        for expected_index in tqdm.tqdm(
            range(self.total_samples), desc="test_next_item"
        ):
            shard_index, sample_index = span(
                expected_index,
                [s.samples for s in iteration.shardsets[0].shards],
            )
            expected_main_shard = iteration.shardsets[0].shards[shard_index]

            item = iteration_state.next_item(rank)
            index = item.index
            main_shard = item.main_shard
            feature_shards = item.feature_shards
            self.assertEqual(main_shard.location, expected_main_shard.location)
            self.assertEqual(len(feature_shards), 0)
            self.assertEqual(index, expected_index)
            self.assertEqual(main_shard.index, shard_index)
            self.assertEqual(main_shard.sample_index, sample_index)
            self.assertEqual(main_shard.location, expected_main_shard.location)
            self.assertEqual(main_shard.format, expected_main_shard.format)
            self.assertEqual(main_shard.filesize, expected_main_shard.filesize)
            self.assertEqual(main_shard.samples, expected_main_shard.samples)

    def test_pop_index_no_shuffle_replication_pg(self):
        ranks = [0, 1, 2, 3, 4, 5, 6, 7]
        replication_pg = [[0, 1], [2, 3], [4, 5], [6, 7]]

        iteration = self.get_iteration(
            "test_pop_index_no_shuffle_replication_pg",
            replication_pg=replication_pg,
        )

        iteration_state = IterationState(iteration.id, self.cache)
        iteration_state.init(iteration)

        retrieved_per_rank = [[] for _ in ranks]
        ranks_done = {rank: False for rank in ranks}
        for i in tqdm.tqdm(
            range(int(self.total_samples * 2 * 1.5)),
            desc="test_pop_index_no_shuffle_multiple_ranks",
        ):
            rank = ranks[i % len(ranks)]
            try:
                retrieved_index = iteration_state._pop_index(rank)
            except IterationStateException:
                ranks_done[rank] = True
                if all(ranks_done.values()):
                    break
                continue
            retrieved_per_rank[rank].append(retrieved_index)

        for pg in replication_pg:
            for rank in pg:
                self.assertEqual(
                    len(retrieved_per_rank[rank]),
                    self.total_samples // len(replication_pg),
                )
            for i in range(len(pg) - 1):
                self.assertEqual(
                    retrieved_per_rank[pg[i]],
                    retrieved_per_rank[pg[i + 1]],
                )

    # TODO with feature shards

    def test_pushback_inprogress(self):
        iteration = self.get_iteration("test_pushback_inprogress")

        iteration_state = IterationState(iteration.id, self.cache)
        iteration_state.init(iteration)

        for i in range(10):
            next_item = iteration_state.next_item(0)
            if i < 5:
                iteration_state.complete(next_item.index)

        progress = iteration_state.get_progress()
        self.assertEqual(progress.current, 10)
        self.assertEqual(progress.completed, 5)

        self.assertEqual(len(progress.inprogress), 5)
        for inprogress in progress.inprogress:
            self.assertGreaterEqual(inprogress.index, 5)
            self.assertEqual(inprogress.rank, 0)

        iteration_state.pushback_inprogress()

        progress = iteration_state.get_progress()
        self.assertEqual(progress.current, 5)
        self.assertEqual(progress.completed, 5)
        self.assertEqual(len(progress.inprogress), 0)
