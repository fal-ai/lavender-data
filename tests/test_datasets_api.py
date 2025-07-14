import unittest
import time
import shutil
import os

from lavender_data.client.api import (
    init,
    create_dataset,
    create_shardset,
    get_dataset,
    get_shardset,
    delete_dataset,
    delete_shardset,
    DatasetColumnOptions,
)

from tests.utils.shards import create_test_shards
from tests.utils.start_server import (
    get_free_port,
    start_server,
    stop_server,
    wait_server_ready,
)


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

    def tearDown(self):
        stop_server(self.server)
        os.remove(self.db)

    def test_create_dataset_and_shardset(self):
        shard_count = 10
        samples_per_shard = 10

        # Create dataset
        dataset_name = f"test-dataset-{time.time()}"
        response = create_dataset(dataset_name, uid_column_name="id")
        dataset_id = response.id

        # Create test data
        location = create_test_shards(dataset_id, shard_count, samples_per_shard)

        # Create shardset containing image_url and caption
        response = create_shardset(
            dataset_id=dataset_id,
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
        shardset_id = response.id

        # Get dataset
        response = get_dataset(dataset_id)
        self.assertEqual(response.id, dataset_id)
        self.assertEqual(response.name, dataset_name)
        self.assertEqual(len(response.columns), 3)
        for column in response.columns:
            self.assertIn(column.name, ["id", "image_url", "caption"])

        # Get shardset
        response = get_shardset(dataset_id, shardset_id)
        self.assertEqual(response.id, shardset_id)
        self.assertEqual(response.dataset_id, dataset_id)
        self.assertEqual(response.location, location)
        self.assertEqual(response.shard_count, shard_count)
        self.assertEqual(response.total_samples, shard_count * samples_per_shard)

        self.assertEqual(len(response.columns), 3)
        for column in response.columns:
            self.assertIn(column.name, ["id", "image_url", "caption"])

        self.assertEqual(response.shard_count, shard_count)
        self.assertEqual(response.total_samples, shard_count * samples_per_shard)

        # Delete shardset
        response = delete_shardset(dataset_id, shardset_id)
        self.assertRaises(Exception, get_shardset, dataset_id, shardset_id)

        # Delete dataset
        response = delete_dataset(dataset_id)
        self.assertRaises(Exception, get_dataset, dataset_id)

        # Clean up
        shutil.rmtree(f".cache/{dataset_id}")

    def test_create_dataset_with_shardset_location(self):
        shard_count = 10
        samples_per_shard = 10

        # Create dataset
        dataset_name = f"test-dataset-{time.time()}"

        # Create test data
        location = create_test_shards(dataset_name, shard_count, samples_per_shard)

        response = create_dataset(
            dataset_name, uid_column_name="id", shardset_location=location
        )
        dataset_id = response.id

        # Create shardset containing image_url and caption
        time.sleep(3)

        # Get dataset
        response = get_dataset(dataset_id)
        self.assertEqual(response.id, dataset_id)
        self.assertEqual(response.name, dataset_name)
        self.assertEqual(len(response.columns), 5)
        for column in response.columns:
            self.assertIn(
                column.name, ["id", "image_url", "caption", "width", "height"]
            )

        # Get shardset
        shardset_id = response.shardsets[0].id
        response = get_shardset(dataset_id, shardset_id)
        self.assertEqual(response.id, shardset_id)
        self.assertEqual(response.dataset_id, dataset_id)
        self.assertEqual(response.location, location)
        self.assertEqual(response.shard_count, shard_count)
        self.assertEqual(response.total_samples, shard_count * samples_per_shard)

        self.assertEqual(len(response.columns), 5)
        for column in response.columns:
            self.assertIn(
                column.name, ["id", "image_url", "caption", "width", "height"]
            )

        self.assertEqual(response.shard_count, shard_count)
        self.assertEqual(response.total_samples, shard_count * samples_per_shard)

        # Clean up
        shutil.rmtree(f".cache/{dataset_name}")

    def test_create_dataset_with_shardset_location_failure(self):
        dataset_name = f"test-dataset-{time.time()}"
        location = ".cache/not-a-real-location"

        self.assertRaises(
            Exception,
            create_dataset,
            dataset_name,
            uid_column_name="id",
            shardset_location=location,
        )
