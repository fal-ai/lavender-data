import os
import csv
import random


def create_test_shards(dataset_id: str, shard_count: int, samples_per_shard: int):
    test_dir = f".cache/{dataset_id}"
    os.makedirs(test_dir, exist_ok=True)
    for i in range(shard_count):
        with open(f"{test_dir}/shard.{i:05d}.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "image_url", "caption", "width", "height"])
            for j in range(samples_per_shard):
                width, height = random.choice([(640, 360), (1280, 720)])
                writer.writerow(
                    [
                        (i * samples_per_shard) + j,
                        f"https://example.com/image-{(i * samples_per_shard) + j:05d}.jpg",
                        f"Caption for image {(i * samples_per_shard) + j:05d}",
                        width,
                        height,
                    ]
                )

    return f"file://{test_dir}"
