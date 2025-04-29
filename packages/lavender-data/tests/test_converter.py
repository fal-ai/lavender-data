import unittest
import tempfile
import tqdm
import random
import os

import lavender_data.client as lavender
from tests.utils.start_server import start_server, wait_server_ready, stop_server


class TestConverter(unittest.TestCase):
    def setUp(self):
        self.port = random.randint(10000, 40000)
        self.db = f"database-{self.port}.db"

        self.server = start_server(
            self.port,
            {
                "LAVENDER_DATA_DISABLE_AUTH": "true",
                "LAVENDER_DATA_DB_URL": f"sqlite:///{self.db}",
                "LAVENDER_DATA_LOG_FILE": "./test.log",
            },
        )
        wait_server_ready(self.server, self.port)

        lavender.init(api_url=f"http://localhost:{self.port}")

    def tearDown(self):
        stop_server(self.server)
        os.remove(self.db)

    def test_wds(self):
        import webdataset as wds

        bucket = "https://storage.googleapis.com/webdataset/testdata/"
        dataset = "publaynet-train-{000000..000009}.tar"

        url = bucket + dataset
        pil_dataset = wds.WebDataset(url).decode("pil")

        max_shard_count = 2
        samples_per_shard = 100
        total_samples = max_shard_count * samples_per_shard
        dataset_name = "publaynet-train"

        with tempfile.TemporaryDirectory() as temp_dir:
            lavender.Converter.get(
                "webdataset",
            ).to_shardset(
                tqdm.tqdm(pil_dataset, total=total_samples),
                dataset_name,
                location=f"file://{temp_dir}/{dataset_name}",
                uid_column_name="id",
                max_shard_count=max_shard_count,
                samples_per_shard=samples_per_shard,
            )

            dataset = lavender.api.get_dataset(name=dataset_name)
            shardset = lavender.api.get_shardset(dataset.id, dataset.shardsets[0].id)

            self.assertEqual(len(shardset.shards), max_shard_count)
            for shard in shardset.shards:
                self.assertTrue(os.path.exists(shard.location.split("file://")[1]))

            sample_count = 0
            for sample in lavender.LavenderDataLoader(dataset_name=dataset_name):
                for key in {
                    "__key__",
                    "id",
                    "file_name",
                    "height",
                    "width",
                    "annotations",
                    "png",
                }:
                    self.assertIn(key, sample)
                sample_count += 1

            self.assertEqual(sample_count, total_samples)
