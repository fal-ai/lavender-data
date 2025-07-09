import unittest
import shutil
import os

import numpy as np

from lavender_data.server.reader import (
    ServerSideReader,
    GlobalSampleIndex,
    MainShardInfo,
    ShardInfo,
    InnerJoinSampleInsufficient,
)

from tests.utils.shards import create_test_shard


class TestReader(unittest.TestCase):
    def setUp(self):
        self.disk_cache_size = 10
        self.reader = ServerSideReader(
            disk_cache_size=self.disk_cache_size, dirname=".cache/reader"
        )

        self.test_dir = ".cache/test-reader"
        os.makedirs(self.test_dir, exist_ok=True)

        self.image_url_shard = f"{self.test_dir}/image_url.csv"
        create_test_shard(
            self.image_url_shard,
            [
                {
                    "id": 0,
                    "image_url": "https://example.com/image-0.jpg",
                },
                {
                    "id": 1,
                    "image_url": "https://example.com/image-1.jpg",
                },
                {
                    "id": 2,
                    "image_url": "https://example.com/image-2.jpg",
                },
            ],
        )

        self.caption_shard = f"{self.test_dir}/caption.csv"
        create_test_shard(
            self.caption_shard,
            [
                {
                    "id": 0,
                    "caption": "Caption for image 0",
                },
                {
                    "id": 2,
                    "caption": "Caption for image 2",
                },
            ],
        )

        self.score_shard = f"{self.test_dir}/score.csv"
        create_test_shard(
            self.score_shard,
            [
                {
                    "id": 1,
                    "score": 0.2,
                },
                {
                    "id": 2,
                    "score": 0.3,
                },
            ],
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)

    def test_get_reader(self):
        reader = self.reader.get_reader(
            ShardInfo(
                shardset_id="test-reader",
                index=0,
                samples=3,
                location=f"file://{self.image_url_shard}",
                format="csv",
                filesize=1,
                columns={"id": "int", "image_url": "string"},
            ),
            "id",
            "int",
        )

        sample = reader.get_item_by_index(0)
        self.assertEqual(sample["id"], 0)
        self.assertEqual(sample["image_url"], "https://example.com/image-0.jpg")

    def test_get_sample(self):
        index = GlobalSampleIndex(
            index=0,
            uid_column_name="id",
            uid_column_type="int",
            main_shard=MainShardInfo(
                shardset_id="test-reader",
                index=0,
                samples=3,
                location=f"file://{self.image_url_shard}",
                format="csv",
                filesize=1,
                columns={"id": "int", "image_url": "string"},
                sample_index=0,
            ),
            feature_shards=[
                ShardInfo(
                    shardset_id="test-reader",
                    index=0,
                    samples=2,
                    location=f"file://{self.caption_shard}",
                    format="csv",
                    filesize=1,
                    columns={"id": "int", "caption": "string"},
                ),
                ShardInfo(
                    shardset_id="test-reader",
                    index=0,
                    samples=2,
                    location=f"file://{self.score_shard}",
                    format="csv",
                    filesize=1,
                    columns={"id": "int", "score": "float"},
                ),
            ],
        )
        sample = self.reader.get_sample(index, join="left")
        self.assertEqual(sample["id"], 0)
        self.assertEqual(sample["image_url"], "https://example.com/image-0.jpg")
        self.assertEqual(sample["caption"], "Caption for image 0")
        self.assertTrue(np.isnan(sample["score"]))

        with self.assertRaises(InnerJoinSampleInsufficient):
            self.reader.get_sample(index, join="inner")

    # TODO cache size test
