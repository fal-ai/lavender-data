import unittest
import time
import random
import shutil
import tqdm
import os

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
from lavender_data.client.api import LavenderDataApiError

from tests.utils.shards import create_test_shards
from tests.utils.start_server import start_server, stop_server, wait_server_ready


class TestFilter(Filter, name="test_filter"):
    def filter(self, sample: dict) -> bool:
        return sample["id"] % 2 == 0


class TestPreprocessor(Preprocessor, name="test_preprocessor"):
    def process(self, sample: dict) -> dict:
        return {"double_id": i * 2 for i in sample["id"]}


class FailOnceInTwoSamples(Preprocessor, name="fail_once_in_two_samples"):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failed = False

    def process(self, sample: dict) -> dict:
        if not self.failed:
            self.failed = True
            raise Exception("Failed to process sample")
        else:
            self.failed = False
            return sample


class TestIteration(unittest.TestCase):
    def setUp(self):
        self.port = random.randint(10000, 40000)
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
                )
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

    def test_iteration_with_batch_size(self):
        read_samples = 0
        batch_size = 10
        for i, batch in tqdm.tqdm(
            enumerate(
                LavenderDataLoader(
                    self.dataset_id,
                    shardsets=[self.shardset_id],
                    batch_size=batch_size,
                )
            ),
            total=self.total_samples // batch_size,
            desc="test_iteration_with_batch_size",
        ):
            self.assertEqual(len(batch["image_url"]), batch_size)
            for j, (image_url, caption) in enumerate(
                zip(batch["image_url"], batch["caption"])
            ):
                self.assertEqual(
                    image_url, f"https://example.com/image-{i * batch_size + j:05d}.jpg"
                )
                self.assertEqual(caption, f"Caption for image {i * batch_size + j:05d}")
                read_samples += 1
        self.assertEqual(read_samples, self.total_samples)

    def test_iteration_with_rank(self):
        rank_1 = LavenderDataLoader(
            dataset_id=self.dataset_id,
            shardsets=[self.shardset_id],
            rank=1,
            world_size=2,
        )
        rank_2 = LavenderDataLoader(
            dataset_id=self.dataset_id,
            shardsets=[self.shardset_id],
            rank=2,
            world_size=2,
        )

        rank_1_samples = []
        rank_2_samples = []
        rank_1_stopped = False
        rank_2_stopped = False
        for i in tqdm.tqdm(
            range(self.total_samples * 2),
            desc="test_iteration_with_rank",
        ):
            if rank_1_stopped and rank_2_stopped:
                break

            if i % 2 == 0:
                try:
                    rank_1_samples.append(next(rank_1))
                except StopIteration:
                    rank_1_stopped = True
            else:
                try:
                    rank_2_samples.append(next(rank_2))
                except StopIteration:
                    rank_2_stopped = True

        rank_1_image_urls = [sample["image_url"] for sample in rank_1_samples]
        rank_2_image_urls = [sample["image_url"] for sample in rank_2_samples]

        self.assertEqual(len(rank_1_image_urls), self.total_samples // 2)
        self.assertEqual(len(rank_2_image_urls), self.total_samples // 2)
        self.assertEqual(len(set(rank_1_image_urls) & set(rank_2_image_urls)), 0)
        self.assertEqual(
            len(set(rank_1_image_urls) | set(rank_2_image_urls)), self.total_samples
        )

    def test_iteration_with_max_retry_count(self):
        self.assertRaises(
            LavenderDataApiError,
            lambda: next(
                LavenderDataLoader(
                    dataset_id=self.dataset_id,
                    shardsets=[self.shardset_id],
                    preprocessors=["fail_once_in_two_samples"],
                    max_retry_count=0,
                    no_cache=True,
                )
            ),
        )

        read_samples = 0
        for i, sample in tqdm.tqdm(
            enumerate(
                LavenderDataLoader(
                    dataset_id=self.dataset_id,
                    shardsets=[self.shardset_id],
                    preprocessors=["fail_once_in_two_samples"],
                    max_retry_count=1,
                    no_cache=True,
                )
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
            LavenderDataApiError,
            lambda: next(
                LavenderDataLoader(
                    dataset_id=self.dataset_id,
                    shardsets=[self.shardset_id],
                    preprocessors=["fail_once_in_two_samples"],
                    skip_on_failure=False,
                )
            ),
        )

        read_samples = 0
        for i, sample in tqdm.tqdm(
            enumerate(
                LavenderDataLoader(
                    dataset_id=self.dataset_id,
                    shardsets=[self.shardset_id],
                    preprocessors=["fail_once_in_two_samples"],
                    skip_on_failure=True,
                )
            ),
            total=self.total_samples,
            desc="test_iteration_with_skip_on_failure",
        ):
            read_samples += 1
        self.assertEqual(read_samples, self.total_samples // 2)

    def test_iteration_with_filter(self):
        read_samples = 0
        for i, sample in tqdm.tqdm(
            enumerate(
                LavenderDataLoader(
                    self.dataset_id,
                    shardsets=[self.shardset_id],
                    filters=[("test_filter", {})],
                )
            ),
            total=self.total_samples // 2,
            desc="test_iteration_with_filter",
        ):
            self.assertEqual(sample["id"] % 2, 0)
            read_samples += 1
        self.assertEqual(read_samples, self.total_samples // 2)

    def test_iteration_with_preprocessor(self):
        read_samples = 0
        for i, sample in tqdm.tqdm(
            enumerate(
                LavenderDataLoader(
                    self.dataset_id,
                    shardsets=[self.shardset_id],
                    preprocessors=[("test_preprocessor", {})],
                )
            ),
            total=self.total_samples,
            desc="test_iteration_with_preprocessor",
        ):
            self.assertEqual(sample["double_id"], i * 2)
            read_samples += 1
        self.assertEqual(read_samples, self.total_samples)

    def test_iteration_torch_dataloader(self):
        read_samples = 0

        dataloader = LavenderDataLoader(
            self.dataset_id,
            shardsets=[self.shardset_id],
        ).torch()

        for i, sample in enumerate(
            tqdm.tqdm(dataloader, desc="test_iteration_torch_dataloader")
        ):
            self.assertEqual(
                sample["image_url"], f"https://example.com/image-{i:05d}.jpg"
            )
            self.assertEqual(sample["caption"], f"Caption for image {i:05d}")
            read_samples += 1
        self.assertEqual(read_samples, self.total_samples)

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
