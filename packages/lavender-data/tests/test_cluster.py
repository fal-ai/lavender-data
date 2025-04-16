import os
import unittest
import random
import time
import shutil
import subprocess

from lavender_data.client import api

from tests.utils.shards import create_test_shards


class TestCluster(unittest.TestCase):
    def setUp(self):
        head_port = random.randint(10000, 40000)
        node_ports = [random.randint(10000, 40000) for _ in range(3)]

        poetry = shutil.which("poetry")
        if poetry is None:
            raise Exception("poetry not found")

        self.head_url = f"http://localhost:{head_port}"
        self.node_urls = [f"http://localhost:{port}" for port in node_ports]
        self.head_db = f"database-{head_port}.db"
        self.node_dbs = [f"database-{port}.db" for port in node_ports]

        self.head_server = subprocess.Popen(
            [
                poetry,
                "run",
                "lavender-data",
                "server",
                "run",
                "--port",
                str(head_port),
                "--disable-ui",
            ],
            env={
                "LAVENDER_DATA_DISABLE_AUTH": "true",
                "LAVENDER_DATA_DB_URL": f"sqlite:///{self.head_db}",
                "LAVENDER_DATA_CLUSTER_ENABLED": "true",
                "LAVENDER_DATA_CLUSTER_HEAD": "true",
                "LAVENDER_DATA_CLUSTER_HEAD_URL": self.head_url,
                "LAVENDER_DATA_CLUSTER_NODE_URL": self.head_url,
            },
        )

        self.node_servers = [
            subprocess.Popen(
                [
                    poetry,
                    "run",
                    "lavender-data",
                    "server",
                    "run",
                    "--port",
                    str(node_port),
                    "--disable-ui",
                ],
                env={
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

        time.sleep(3)

    def tearDown(self):
        for node_server in self.node_servers:
            node_server.terminate()
        time.sleep(1)
        self.head_server.terminate()
        time.sleep(2)
        for node_db in self.node_dbs:
            os.remove(node_db)
        os.remove(self.head_db)

    def test_registered(self):
        head = api.LavenderDataClient(self.head_url)
        node_statuses = head.get_node_statuses()
        self.assertEqual(len(node_statuses), len(self.node_urls))

        node_urls = [node.node_url for node in node_statuses]
        self.assertEqual(set(node_urls), set(self.node_urls))

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
