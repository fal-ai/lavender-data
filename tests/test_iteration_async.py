import unittest
import time
import random
import shutil
import tqdm
import os
import sys

from lavender_data.server import (
    Preprocessor,
    Filter,
)
from lavender_data.client.api import (
    init,
    create_dataset,
    create_shardset,
    DatasetColumnOptions,
)
from lavender_data.client import LavenderDataLoader

from tests.utils.shards import create_test_shards
from tests.utils.start_server import (
    get_free_port,
    start_server,
    stop_server,
    wait_server_ready,
)


class TestFilter(Filter, name="test_filter"):
    def filter(self, sample: dict) -> bool:
        return sample["id"] % 2 == 0


class TestPreprocessor(Preprocessor, name="test_preprocessor"):
    def process(self, sample: dict) -> dict:
        return {"double_id": i * 2 for i in sample["id"]}


class Fail25PercentSamples(Preprocessor, name="fail_25_percent_samples"):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process(self, sample: dict) -> dict:
        if random.random() < 0.25:
            raise Exception("Failed to process sample")
        return sample


class FailEvenSamples(Preprocessor, name="fail_even_samples"):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process(self, sample: dict) -> dict:
        if sample["id"] % 2 == 0:
            raise Exception("Failed to process sample")
        return sample


class TestIterationAsync(unittest.TestCase):
    def setUp(self):
        self.port = get_free_port()
        self.db = f"database-{self.port}.db"

        self.server = start_server(
            self.port,
            {
                "LAVENDER_DATA_DISABLE_AUTH": "true",
                "LAVENDER_DATA_DB_URL": f"sqlite:///{self.db}",
                "LAVENDER_DATA_MODULES_DIR": "./tests/",
            },
        )
        wait_server_ready(self.server, self.port)

        self.api_url = f"http://localhost:{self.port}"
        init(api_url=self.api_url)

        shard_count = 10
        samples_per_shard = 10
        self.total_samples = shard_count * samples_per_shard

        # Create dataset
        response = create_dataset(f"test-dataset-{time.time()}", uid_column_name="id")
        self.dataset_id = response.id

        # Create test data
        location = create_test_shards(self.dataset_id, shard_count, samples_per_shard)

        # Create shardset containing image_url and caption
        response = create_shardset(
            dataset_id=self.dataset_id,
            location=location,
            columns=[
                DatasetColumnOptions(
                    name="id",
                    description="An id",
                    type_="int",
                ),
                DatasetColumnOptions(
                    name="image_url",
                    description="An image url",
                    type_="text",
                ),
                DatasetColumnOptions(
                    name="caption",
                    description="A caption for the image",
                    type_="text",
                ),
            ],
        )
        time.sleep(3)
        self.shardset_id = response.id

    def tearDown(self):
        shutil.rmtree(f".cache/{self.dataset_id}")
        stop_server(self.server)
        os.remove(self.db)

    def test_iteration(self):
        read_samples = 0
        for i, sample in tqdm.tqdm(
            enumerate(
                LavenderDataLoader(
                    dataset_id=self.dataset_id, shardsets=[self.shardset_id]
                ).to_async(prefetch_factor=4, in_order=True)
            ),
            total=self.total_samples,
            desc="test_iteration",
        ):
            self.assertEqual(
                sample["image_url"], f"https://example.com/image-{i:05d}.jpg"
            )
            self.assertEqual(sample["caption"], f"Caption for image {i:05d}")
            read_samples += 1
        self.assertEqual(read_samples, self.total_samples)

    def test_iteration_with_max_retry_count(self):
        self.assertRaises(
            Exception,
            lambda: next(
                iter(
                    LavenderDataLoader(
                        dataset_id=self.dataset_id,
                        shardsets=[self.shardset_id],
                        preprocessors=["fail_once_in_two_samples"],
                        max_retry_count=0,
                    ).to_async(prefetch_factor=4)
                )
            ),
        )

        read_samples = 0
        for i, sample in tqdm.tqdm(
            enumerate(
                LavenderDataLoader(
                    dataset_id=self.dataset_id,
                    shardsets=[self.shardset_id],
                    preprocessors=["fail_25_percent_samples"],
                    max_retry_count=8,
                ).to_async(prefetch_factor=4, in_order=True)
            ),
            total=self.total_samples,
            desc="test_iteration_with_max_retry_count",
        ):
            self.assertEqual(
                sample["image_url"], f"https://example.com/image-{i:05d}.jpg"
            )
            self.assertEqual(sample["caption"], f"Caption for image {i:05d}")
            read_samples += 1
        self.assertEqual(read_samples, self.total_samples)

    def test_iteration_with_skip_on_failure(self):
        self.assertRaises(
            Exception,
            lambda: next(
                iter(
                    LavenderDataLoader(
                        dataset_id=self.dataset_id,
                        shardsets=[self.shardset_id],
                        preprocessors=["fail_even_samples"],
                        skip_on_failure=False,
                    ).to_async(prefetch_factor=4)
                )
            ),
        )

        read_samples = 0
        for i, sample in tqdm.tqdm(
            enumerate(
                LavenderDataLoader(
                    dataset_id=self.dataset_id,
                    shardsets=[self.shardset_id],
                    preprocessors=["fail_even_samples"],
                    skip_on_failure=True,
                ).to_async(prefetch_factor=4)
            ),
            total=self.total_samples,
            desc="test_iteration_with_skip_on_failure",
        ):
            read_samples += 1
        self.assertEqual(read_samples, self.total_samples // 2)

    def test_iteration_torch_dataloader_with_prefetch_factor(self):
        read_samples = 0

        dataloader = LavenderDataLoader(
            self.dataset_id,
            shardsets=[self.shardset_id],
            api_url=self.api_url,
        ).torch(
            prefetch_factor=4,
        )

        for i, sample in enumerate(
            tqdm.tqdm(
                dataloader, desc="test_iteration_torch_dataloader_with_prefetch_factor"
            )
        ):
            self.assertEqual(
                sample["image_url"], f"https://example.com/image-{i:05d}.jpg"
            )
            self.assertEqual(sample["caption"], f"Caption for image {i:05d}")
            read_samples += 1
        self.assertEqual(read_samples, self.total_samples)
