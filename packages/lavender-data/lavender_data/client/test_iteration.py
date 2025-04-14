import unittest
import time
import random
import csv
import os
import shutil
import tqdm
from multiprocessing import Process

import uvicorn
from lavender_data.server import (
    app,
    Preprocessor,
    Filter,
)
from lavender_data.server.scripts.create_api_key import create_api_key
from lavender_data.client.api import (
    init,
    create_dataset,
    create_shardset,
    DatasetColumnOptions,
    create_shard,
)
from lavender_data.client.iteration import Iteration


def run_server(port: int):
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")


class TestFilter(Filter, name="test_filter"):
    def filter(self, sample: dict) -> bool:
        return sample["id"] % 2 == 0


class TestPreprocessor(Preprocessor, name="test_preprocessor"):
    def process(self, sample: dict) -> dict:
        return {"double_id": i * 2 for i in sample["id"]}


class TestIteration(unittest.TestCase):
    def setUp(self):
        port = random.randint(10000, 40000)
        self.server = Process(
            target=run_server,
            args=(port,),
            daemon=True,
        )
        self.server.start()

        time.sleep(2)

        api_key = create_api_key()
        init(
            api_url=f"http://localhost:{port}",
            api_key=f"{api_key.id}:{api_key.secret}",
        )

        shard_count = 10
        samples_per_shard = 10
        self.total_samples = shard_count * samples_per_shard

        # Create dataset
        response = create_dataset(f"test-dataset-{time.time()}", uid_column_name="id")
        self.dataset_id = response.id

        # Create test data
        test_dir = f".cache/{self.dataset_id}"
        os.makedirs(test_dir, exist_ok=True)
        for i in range(shard_count):
            with open(f"{test_dir}/shard.{i:05d}.csv", "w") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "image_url", "caption"])
                for j in range(samples_per_shard):
                    writer.writerow(
                        [
                            (i * samples_per_shard) + j,
                            f"https://example.com/image-{(i * samples_per_shard) + j:05d}.jpg",
                            f"Caption for image {(i * samples_per_shard) + j:05d}",
                        ]
                    )

        # Create shardset containing image_url and caption
        response = create_shardset(
            dataset_id=self.dataset_id,
            location=f"file://{test_dir}",
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
        self.shardset_id = response.id

    def tearDown(self):
        shutil.rmtree(f".cache/{self.dataset_id}")
        self.server.terminate()

    def test_iteration(self):
        read_samples = 0
        for i, sample in tqdm.tqdm(
            enumerate(
                Iteration.from_dataset(
                    dataset_id=self.dataset_id, shardsets=[self.shardset_id]
                )
            ),
            total=self.total_samples,
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
                Iteration.from_dataset(
                    self.dataset_id,
                    shardsets=[self.shardset_id],
                    batch_size=batch_size,
                )
            ),
            total=self.total_samples // batch_size,
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

    def test_iteration_with_filter(self):
        read_samples = 0
        for i, sample in tqdm.tqdm(
            enumerate(
                Iteration.from_dataset(
                    self.dataset_id,
                    shardsets=[self.shardset_id],
                    filters=[("test_filter", {})],
                )
            ),
            total=self.total_samples // 2,
        ):
            self.assertEqual(sample["id"] % 2, 0)
            read_samples += 1
        self.assertEqual(read_samples, self.total_samples // 2)

    def test_iteration_with_preprocessor(self):
        read_samples = 0
        for i, sample in tqdm.tqdm(
            enumerate(
                Iteration.from_dataset(
                    self.dataset_id,
                    shardsets=[self.shardset_id],
                    preprocessors=[("test_preprocessor", {})],
                )
            ),
            total=self.total_samples,
        ):
            self.assertEqual(sample["double_id"], i * 2)
            read_samples += 1
        self.assertEqual(read_samples, self.total_samples)
