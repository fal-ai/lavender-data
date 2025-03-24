import tqdm
import unittest
import time

from lavender_data.client.api import (
    create_dataset,
    create_shardset,
    DatasetColumnOptions,
    create_shard,
    create_iteration,
    get_next_item,
)


class TestAPI(unittest.TestCase):
    def test_iteration(self):
        shard_count = 50
        samples_per_shard = 100

        # Create dataset
        response = create_dataset(f"test-dataset-{time.time()}")
        dataset_id = response.id

        # Create shardset containing image_url and caption
        response = create_shardset(
            dataset_id=dataset_id,
            location="s3://test-shardset/images",
            columns=[
                DatasetColumnOptions(
                    name="caption",
                    description="A caption for the image",
                    type_="text",
                ),
                DatasetColumnOptions(
                    name="image_url",
                    description="An image url",
                    type_="text",
                ),
            ],
        )
        shardset_id = response.id

        # Create shards
        for shard_index in range(shard_count):
            response = create_shard(
                dataset_id=dataset_id,
                shardset_id=shardset_id,
                index=shard_index,
                location=f"s3://test-shardset/images/shard.{shard_index:05d}.parquet",
                filesize=1024 * 1024 * 10,
                samples=samples_per_shard,
                format="parquet",
            )

        # Create shardset containing matching_score
        response = create_shardset(
            dataset_id=dataset_id,
            location="s3://test-shardset/matching_scores",
            columns=[
                DatasetColumnOptions(
                    name="matching_score",
                    description="A matching score",
                    type_="float",
                ),
            ],
        )
        shardset_id = response.id

        # Create shards
        for shard_index in range(shard_count):
            response = create_shard(
                dataset_id=dataset_id,
                shardset_id=shardset_id,
                index=shard_index,
                location=f"s3://test-shardset/matching_scores/shard.{shard_index:05d}.parquet",
                filesize=1024 * 1024 * 1,
                samples=samples_per_shard,
                format="parquet",
            )

        # Create iteration
        response = create_iteration(
            dataset_id=dataset_id,
            shuffle=True,
            shuffle_seed=0,
            shuffle_block_size=10,
            batch_size=0,
        )
        iteration_id = response.id

        # Get next item
        for i in tqdm.tqdm(range(shard_count * samples_per_shard)):
            response = get_next_item(iteration_id=iteration_id)
            break

    def test_iteration_replication_pg(self):
        shard_count = 50
        samples_per_shard = 100

        # Create dataset
        response = create_dataset(name=f"test-dataset-{time.time()}")
        dataset_id = response.id

        # Create shardset containing image_url and caption
        response = create_shardset(
            dataset_id=dataset_id,
            location="s3://test-shardset/images",
            columns=[
                DatasetColumnOptions(
                    name="caption",
                    description="A caption for the image",
                    type_="text",
                ),
                DatasetColumnOptions(
                    name="image_url",
                    description="An image url",
                    type_="text",
                ),
            ],
        )
        shardset_id = response.id

        # Create shards
        for shard_index in range(shard_count):
            response = create_shard(
                dataset_id=dataset_id,
                shardset_id=shardset_id,
                index=shard_index,
                location=f"s3://test-shardset/images/shard.{shard_index:05d}.parquet",
                filesize=1024 * 1024 * 10,
                samples=samples_per_shard,
                format="parquet",
            )

        # Create shardset containing matching_score
        response = create_shardset(
            dataset_id=dataset_id,
            location="s3://test-shardset/matching_scores",
            columns=[
                DatasetColumnOptions(
                    name="matching_score",
                    description="A matching score",
                    type_="float",
                ),
            ],
        )
        shardset_id = response.id

        # Create shards
        for shard_index in range(shard_count):
            response = create_shard(
                dataset_id=dataset_id,
                shardset_id=shardset_id,
                index=shard_index,
                location=f"s3://test-shardset/matching_scores/shard.{shard_index:05d}.parquet",
                filesize=1024 * 1024 * 1,
                samples=samples_per_shard,
                format="parquet",
            )

        # Create iteration
        response = create_iteration(
            dataset_id=dataset_id,
            shuffle=True,
            shuffle_seed=0,
            shuffle_block_size=10,
            replication_pg=[[0, 1], [2, 3], [4, 5], [6, 7]],
            batch_size=0,
        )
        iteration_id = response.id

        response = get_next_item(iteration_id=iteration_id, rank=0)
