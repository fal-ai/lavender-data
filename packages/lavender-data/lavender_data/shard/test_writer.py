import io
import os
import unittest
import time
import numpy as np
import uvicorn
import random
from multiprocessing import Process

from lavender_data.server import app
from lavender_data.client.iteration import Iteration
from lavender_data.client.api import (
    init,
    create_dataset,
    get_dataset,
    create_shardset,
    create_iteration,
    DatasetColumnOptions,
)
from lavender_data.shard.writers import Writer

from dotenv import load_dotenv


load_dotenv()


def run_server(port: int):
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")


class NpySerializer:
    format: str = "npy"

    def serialize(self, ndarray: np.ndarray) -> bytes:
        memfile = io.BytesIO()
        np.save(memfile, ndarray)
        return memfile.getvalue()

    def deserialize(self, data: bytes) -> np.ndarray:
        memfile = io.BytesIO(data)
        return np.load(memfile)


class TestWriter(unittest.TestCase):
    def setUp(self):
        port = random.randint(10000, 40000)
        self.server = Process(
            target=run_server,
            args=(port,),
            daemon=True,
        )
        self.server.start()

        time.sleep(2)

        init(api_url=f"http://localhost:{port}")

        # Create a test dataset
        response = create_dataset(
            f"test-shard-writer-dataset-{time.time()}", uid_column_name="number"
        )
        self.dataset_id = response.id

        # Create a shardset
        self.shardset = create_shardset(
            dataset_id=self.dataset_id,
            location="file://" + os.path.join(".cache", "lavender-data", "test_shards"),
            columns=[
                DatasetColumnOptions(
                    name="text",
                    description="A text field",
                    type_="str",
                ),
                DatasetColumnOptions(
                    name="number",
                    description="A numeric field",
                    type_="int",
                ),
                DatasetColumnOptions(
                    name="array",
                    description="A numpy array field",
                    type_="ndarray",
                ),
            ],
        )
        self.shardset_id = self.shardset.id

        self.sample_count_limit = 10
        self.total_samples = 50
        self.serializer = NpySerializer()

        # Create a ShardWriter with a sample count limit
        writer = Writer.get(
            format="csv",
            dataset_id=self.dataset_id,
            shardset_id=self.shardset_id,
            persist_files=True,
        )

        samples = []
        for i in range(self.total_samples):
            samples.append(
                {
                    "text": f"Sample {i}",
                    "number": i,
                    "array": self.serializer.serialize(np.array([i, i + 1, i + 2])),
                }
            )

        for shard_index in range(self.total_samples // self.sample_count_limit):
            writer.write(
                shard_index=shard_index,
                samples=samples[
                    shard_index
                    * self.sample_count_limit : (shard_index + 1)
                    * self.sample_count_limit
                ],
            )

    def test_write_single_shardset(self):
        # Verify the dataset was updated with the correct number of shards
        dataset = get_dataset(self.dataset_id)
        shardset = next(s for s in dataset.shardsets if s.id == self.shardset_id)

        # We expect ceil(total_samples / sample_count_limit) shards
        expected_shard_count = (
            self.total_samples + self.sample_count_limit - 1
        ) // self.sample_count_limit
        self.assertEqual(shardset.shard_count, expected_shard_count)

        # Verify total sample count
        self.assertEqual(shardset.total_samples, self.total_samples)

        read_samples = 0
        for i, sample in enumerate(
            Iteration.from_dataset(self.dataset_id, shardsets=[self.shardset_id])
        ):
            self.assertEqual(sample["text"], f"Sample {i}")
            self.assertEqual(sample["number"], i)
            self.assertTrue(
                np.array_equal(
                    self.serializer.deserialize(sample["array"]),
                    np.array([i, i + 1, i + 2]),
                )
            )
            read_samples += 1
        self.assertEqual(read_samples, self.total_samples)
