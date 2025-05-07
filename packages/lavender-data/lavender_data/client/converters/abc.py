import os
import time
import math
import tempfile
from typing import Iterable, Optional
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed

import pyarrow as pa
import pyarrow.parquet as pq

from lavender_data.client import get_client
from lavender_data.storage import upload_file


class Converter(ABC):
    name: str
    default_uid_column_name: Optional[str] = None

    @classmethod
    def get(cls, name: str, *, max_workers: int = 10) -> "Converter":
        for subcls in cls.__subclasses__():
            if subcls.name == name:
                return subcls(max_workers=max_workers)
        raise ValueError(f"Unsupported converter: {name}")

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers

    def _shard_location(self, location: str, shard_index: int) -> str:
        return os.path.join(location, f"shard.{shard_index:05d}.parquet")

    def to_shard(
        self,
        samples: list[dict],
        location: str,
        shard_index: int,
    ):
        with tempfile.NamedTemporaryFile() as temp_file:
            shard_location = self._shard_location(location, shard_index)
            try:
                table = pa.Table.from_pylist(samples)
            except pa.ArrowTypeError as e:
                type_map = {}
                for i, sample in enumerate(samples):
                    for k, v in sample.items():
                        if k not in type_map:
                            type_map[k] = type(v)

                        if type(v) == type_map[k]:
                            continue

                        # convert float nan to None
                        if isinstance(v, float) and math.isnan(v):
                            samples[i][k] = None
                            continue

                        raise Exception(
                            f"Type mismatch for column {k}: expected {type_map[k]}, got {type(v)} ({v})"
                        ) from e

                # fixed potential type issues, try again
                table = pa.Table.from_pylist(samples)

            pq.write_table(table, temp_file.name)
            upload_file(local_path=temp_file.name, remote_path=shard_location)

    @abstractmethod
    def transform(self, sample: dict) -> dict: ...

    def to_shardset(
        self,
        iterable: Iterable[dict],
        dataset_name: str,
        location: str,
        uid_column_name: Optional[str] = None,
        samples_per_shard: int = 1000,
        max_shard_count: Optional[int] = None,
    ):
        executor = ThreadPoolExecutor(max_workers=self.max_workers)

        futures = []
        shard_index = 0
        samples = []
        for sample in iterable:
            samples.append(self.transform(sample))
            if len(samples) >= samples_per_shard:
                futures.append(
                    executor.submit(
                        self.to_shard,
                        samples=samples,
                        location=location,
                        shard_index=shard_index,
                    )
                )
                samples = []
                shard_index += 1

                if max_shard_count and shard_index >= max_shard_count:
                    break

                while len(futures) > self.max_workers:
                    for future in as_completed(futures):
                        future.result()
                        futures.remove(future)

        if len(samples) > 0:
            futures.append(
                executor.submit(
                    self.to_shard,
                    samples=samples,
                    location=location,
                    shard_index=shard_index,
                )
            )

        print(f"Waiting for shards to be created at {location}")

        for future in as_completed(futures):
            future.result()

        print(f"{shard_index} shards are created at {location}")

        try:
            api = get_client()
        except Exception as e:
            print(f"Failed to connect to Lavender Data API: {e}")
            return

        try:
            dataset = api.get_dataset(name=dataset_name)
        except Exception as e:
            api.create_dataset(
                name=dataset_name,
                uid_column_name=uid_column_name or self.default_uid_column_name,
            )
            dataset = api.get_dataset(name=dataset_name)
            print(f"Dataset {dataset_name} created")

        shardset = next(
            (s for s in dataset.shardsets if s.location == location),
            None,
        )
        if shardset is None:
            shardset = api.create_shardset(
                dataset_id=dataset.id,
                location=location,
            )
            print(f"Shardset {location} created")
        else:
            api.sync_shardset(
                dataset_id=dataset.id,
                shardset_id=shardset.id,
                overwrite=True,
            )

        print(f"Syncing shardset {shardset.id} with {location}")
        while True:
            status = api.get_sync_shardset_status(
                dataset_id=dataset.id, shardset_id=shardset.id
            )
            if status.status == "done":
                break
            time.sleep(1)

        return api.get_shardset(dataset_id=dataset.id, shardset_id=shardset.id)
