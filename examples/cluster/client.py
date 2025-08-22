import os
import csv
import time
import random

import lavender_data.client as lavender


def create_test_shards(dirname: str, shard_count: int, samples_per_shard: int):
    os.makedirs(dirname, exist_ok=True)
    for i in range(shard_count):
        with open(f"{dirname}/shard.{i:05d}.csv", "w") as f:
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


if __name__ == "__main__":
    api_urls = [
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8002",
    ]

    dataset_name = f"test-dataset-{time.time()}"
    dataset = lavender.api.create_dataset(name=dataset_name, uid_column_name="id")

    dirname = os.path.abspath(f".cache/shards/")
    create_test_shards(
        dirname=dirname,
        shard_count=10,
        samples_per_shard=100,
    )
    shard_location = f"file://{dirname}"
    lavender.api.create_shardset(
        dataset_id=dataset.id,
        location=shard_location,
        columns=[
            lavender.api.DatasetColumnOptions(
                name="id",
                type_="int",
            ),
            lavender.api.DatasetColumnOptions(
                name="image_url",
                type_="string",
            ),
            lavender.api.DatasetColumnOptions(
                name="caption",
                type_="string",
            ),
        ],
    )
    print(f"Dataset created: {dataset_name}")

    dls = [
        lavender.LavenderDataLoader(
            dataset_id=dataset.id,
            api_url=api_url,
        )
        for api_url in api_urls
    ]

    for i in range(len(dls[0])):
        dl = random.choice(dls)
        sample = next(dl)

        print(f"Sample {i} from {dl.api_url}: {sample}")
