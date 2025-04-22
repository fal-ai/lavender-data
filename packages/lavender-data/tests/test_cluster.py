import os
import unittest
import random
import time
import tqdm

from lavender_data.client import api, LavenderDataLoader

from tests.utils.shards import create_test_shards
from tests.utils.start_server import start_server, stop_server, wait_server_ready


class TestCluster(unittest.TestCase):
    def setUp(self):
        head_port = random.randint(10000, 40000)
        node_ports = [random.randint(10000, 40000) for _ in range(3)]

        self.head_url = f"http://localhost:{head_port}"
        self.node_urls = [f"http://localhost:{port}" for port in node_ports]
        self.head_db = f"database-{head_port}.db"
        self.node_dbs = [f"database-{port}.db" for port in node_ports]

        self.head_server = start_server(
            head_port,
            {
                "LAVENDER_DATA_DISABLE_AUTH": "true",
                "LAVENDER_DATA_DB_URL": f"sqlite:///{self.head_db}",
                "LAVENDER_DATA_CLUSTER_ENABLED": "true",
                "LAVENDER_DATA_CLUSTER_HEAD": "true",
                "LAVENDER_DATA_CLUSTER_HEAD_URL": self.head_url,
                "LAVENDER_DATA_CLUSTER_NODE_URL": self.head_url,
            },
        )

        self.node_servers = [
            start_server(
                node_port,
                {
                    "LAVENDER_DATA_DISABLE_AUTH": "true",
                    "LAVENDER_DATA_DB_URL": f"sqlite:///{node_db}",
                    "LAVENDER_DATA_CLUSTER_ENABLED": "true",
                    "LAVENDER_DATA_CLUSTER_HEAD": "false",
                    "LAVENDER_DATA_CLUSTER_HEAD_URL": self.head_url,
                    "LAVENDER_DATA_CLUSTER_NODE_URL": node_url,
                },
            )
            for node_url, node_port, node_db in zip(
                self.node_urls, node_ports, self.node_dbs
            )
        ]

        wait_server_ready(self.head_server)
        for node_server in self.node_servers:
            wait_server_ready(node_server)

    def tearDown(self):
        for node_server in self.node_servers:
            stop_server(node_server)
        stop_server(self.head_server)
        for node_db in self.node_dbs:
            os.remove(node_db)
        os.remove(self.head_db)

    def test_registered(self):
        head = api.LavenderDataClient(self.head_url)
        node_statuses = head.get_node_statuses()
        self.assertEqual(len(node_statuses), len(self.node_urls) + 1)

        node_urls = [node.node_url for node in node_statuses]
        self.assertEqual(set(node_urls), set(self.node_urls + [self.head_url]))

    def test_sync_changes_dataset(self):
        head = api.LavenderDataClient(self.head_url)
        dataset = head.create_dataset("test-dataset")

        location = create_test_shards(dataset.id, 10, 10)
        shardset = head.create_shardset(dataset.id, location)

        for node_url in self.node_urls:
            node = api.LavenderDataClient(node_url)
            retreived_dataset = node.get_dataset(dataset.id)
            self.assertEqual(retreived_dataset.id, dataset.id)
            self.assertEqual(len(retreived_dataset.shardsets), 1)
            self.assertEqual(retreived_dataset.shardsets[0].id, shardset.id)

    def test_iteration(self):
        head = api.LavenderDataClient(self.head_url)

        # Create dataset
        shard_count = 10
        samples_per_shard = 10
        total_samples = shard_count * samples_per_shard
        response = head.create_dataset(f"test-dataset-{time.time()}", "id")
        dataset_id = response.id

        # Create test data
        location = create_test_shards(dataset_id, shard_count, samples_per_shard)

        # Create shardset containing image_url and caption
        response = head.create_shardset(
            dataset_id=dataset_id,
            location=location,
            columns=[
                api.DatasetColumnOptions(name="id", type_="int"),
                api.DatasetColumnOptions(name="image_url", type_="text"),
                api.DatasetColumnOptions(name="caption", type_="text"),
            ],
        )
        shardset_id = response.id

        # wait until shardset is synced
        time.sleep(1)

        iteration_from_nodes = [
            LavenderDataLoader(
                dataset_id=dataset_id,
                shardsets=[shardset_id],
                api_url=url,
                cluster_sync=True,
            )
            for url in [self.head_url, *self.node_urls]
        ]

        self.assertEqual(
            len(set(iteration.id for iteration in iteration_from_nodes)), 1
        )

        read_samples = 0
        for i in tqdm.tqdm(range(total_samples)):
            iteration = random.choice(iteration_from_nodes)
            sample = next(iteration)
            self.assertEqual(
                sample["image_url"], f"https://example.com/image-{i:05d}.jpg"
            )
            self.assertEqual(sample["caption"], f"Caption for image {i:05d}")
            read_samples += 1
        self.assertEqual(read_samples, total_samples)

        time.sleep(1)
