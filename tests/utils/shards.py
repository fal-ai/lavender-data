import os
import csv
import random


def create_test_shard(path: str, samples: list[dict]):
    with open(path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=list(samples[0].keys()))
        writer.writeheader()
        writer.writerows(samples)


def create_test_shards(dataset_id: str, shard_count: int, samples_per_shard: int):
    test_dir = f".cache/{dataset_id}"
    os.makedirs(test_dir, exist_ok=True)
    for i in range(shard_count):
        create_test_shard(
            f"{test_dir}/shard.{i:05d}.csv",
            [
                {
                    "id": (i * samples_per_shard) + j,
                    "image_url": f"https://example.com/image-{(i * samples_per_shard) + j:05d}.jpg",
                    "caption": f"Caption for image {(i * samples_per_shard) + j:05d}",
                    "width": random.choice([640, 1280]),
                    "height": random.choice([360, 720]),
                }
                for j in range(samples_per_shard)
            ],
        )
    return f"file://{test_dir}"
