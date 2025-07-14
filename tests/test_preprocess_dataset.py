import time
import unittest
import os
import shutil
import pyarrow.parquet as pq

from lavender_data.server.registries import Preprocessor
from lavender_data.client.api import (
    init,
    create_dataset,
    create_shardset,
    DatasetColumnOptions,
    preprocess_dataset,
    IterationPreprocessor,
    get_tasks,
)

from tests.utils.shards import create_test_shard
from tests.utils.start_server import (
    get_free_port,
    start_server,
    stop_server,
    wait_server_ready,
)


class ConcatPreprocessor(Preprocessor):
    name = "concat"

    def process(self, batch: dict, *, concat: str = "") -> dict:
        batch["concat"] = [c + concat for c in batch["caption"]]
        return batch


class ErrorPreprocessor(Preprocessor):
    name = "error"

    def process(self, batch: dict) -> dict:
        raise Exception("Error")


class TestPreprocessDataset(unittest.TestCase):
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

        response = create_dataset(f"test-dataset-{time.time()}", uid_column_name="id")
        self.dataset_id = response.id

        self.test_dir = ".cache/test-generate-shardset"
        os.makedirs(self.test_dir, exist_ok=True)

        self.image_url_shardset = f"{self.test_dir}/image_url"
        os.makedirs(self.image_url_shardset, exist_ok=True)
        create_test_shard(
            f"{self.image_url_shardset}/0.csv",
            [
                {"id": 0, "image_url": "https://example.com/image-0.jpg"},
                {"id": 1, "image_url": "https://example.com/image-1.jpg"},
                {"id": 2, "image_url": "https://example.com/image-2.jpg"},
            ],
        )
        create_test_shard(
            f"{self.image_url_shardset}/1.csv",
            [
                {"id": 3, "image_url": "https://example.com/image-3.jpg"},
                {"id": 4, "image_url": "https://example.com/image-4.jpg"},
                {"id": 5, "image_url": "https://example.com/image-5.jpg"},
            ],
        )
        response = create_shardset(
            dataset_id=self.dataset_id,
            location=f"file://{self.image_url_shardset}",
            columns=[
                DatasetColumnOptions(name="id", type_="int"),
                DatasetColumnOptions(name="image_url", type_="text"),
            ],
        )
        self.image_url_shardset_id = response.id

        self.caption_shardset = f"{self.test_dir}/caption"
        os.makedirs(self.caption_shardset, exist_ok=True)
        create_test_shard(
            f"{self.caption_shardset}/0.csv",
            [
                {"id": 0, "caption": "Caption for image 0"},
                {"id": 2, "caption": "Caption for image 2"},
            ],
        )
        create_test_shard(
            f"{self.caption_shardset}/1.csv",
            [
                {"id": 3, "caption": "Caption for image 3"},
                {"id": 4, "caption": "Caption for image 4"},
            ],
        )
        response = create_shardset(
            dataset_id=self.dataset_id,
            location=f"file://{self.caption_shardset}",
            columns=[
                DatasetColumnOptions(name="id", type_="int"),
                DatasetColumnOptions(name="caption", type_="text"),
            ],
        )
        self.caption_shardset_id = response.id

        time.sleep(1)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        stop_server(self.server)
        os.remove(self.db)

    def test_preprocess_dataset(self):
        output_dir = f"{self.test_dir}/output"
        os.makedirs(output_dir, exist_ok=True)

        response = preprocess_dataset(
            dataset_id=self.dataset_id,
            shardset_location=f"file://{output_dir}",
            source_shardset_ids=[self.image_url_shardset_id, self.caption_shardset_id],
            preprocessors=[
                IterationPreprocessor.from_dict(
                    {"name": "concat", "params": {"concat": "!!!"}}
                )
            ],
            export_columns=["concat"],
            batch_size=1,
        )
        task_id = response.task_id

        timeout = 10
        start = time.time()
        while True:
            tasks = get_tasks()
            task = next((t for t in tasks if t.task_id == task_id), None)
            if task is None or task.status == "completed":
                break
            time.sleep(1)
            if time.time() - start > timeout:
                raise Exception(
                    f"Timeout waiting for task to complete after {timeout} seconds"
                )

        self.assertEqual(len(os.listdir(output_dir)), 2)

        shard_1 = os.path.join(output_dir, "shard.00000.parquet")
        samples_1 = pq.read_table(shard_1).to_pydict()
        self.assertEqual(samples_1["id"], [0, 1, 2])
        self.assertEqual(
            samples_1["concat"],
            [
                "Caption for image 0!!!",
                "!!!",
                "Caption for image 2!!!",
            ],
        )

        shard_2 = os.path.join(output_dir, "shard.00001.parquet")
        samples_2 = pq.read_table(shard_2).to_pydict()
        self.assertEqual(samples_2["id"], [3, 4, 5])
        self.assertEqual(
            samples_2["concat"],
            ["Caption for image 3!!!", "Caption for image 4!!!", "!!!"],
        )

    def test_preprocess_dataset_with_error(self):
        output_dir = f"{self.test_dir}/output-with-error"
        os.makedirs(output_dir, exist_ok=True)

        response = preprocess_dataset(
            dataset_id=self.dataset_id,
            shardset_location=f"file://{output_dir}",
            source_shardset_ids=[self.image_url_shardset_id, self.caption_shardset_id],
            preprocessors=[
                IterationPreprocessor.from_dict(
                    {"name": "concat", "params": {"concat": "!!!"}}
                ),
                IterationPreprocessor.from_dict({"name": "error", "params": {}}),
            ],
            export_columns=["concat"],
            batch_size=1,
        )
        task_id = response.task_id

        time.sleep(3)

        # TODO
