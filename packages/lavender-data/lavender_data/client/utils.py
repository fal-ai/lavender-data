import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from lavender_data.client import api
from lavender_data.storage import list_files

from lavender_data.shard import inspect_shard


def sync_shard_location(
    dataset_id: str,
    shardset_id: str,
    shard_location: str,
    shard_index: int,
):
    orphan_shard = inspect_shard(shard_location)
    return api.create_shard(
        dataset_id=dataset_id,
        shardset_id=shardset_id,
        location=orphan_shard.location,
        filesize=orphan_shard.filesize,
        samples=orphan_shard.samples,
        format=orphan_shard.format,
        index=shard_index,
        overwrite=True,
    )


def sync_shardset_location(
    dataset_id: str,
    shardset_id: str,
    num_workers: int = 10,
    skip_existing: bool = True,
) -> str:
    shardset = api.get_shardset(dataset_id, shardset_id)

    shard_basenames = sorted(list_files(shardset.location))

    if skip_existing:
        shard_basenames = [
            shard_basename
            for shard_basename in shard_basenames
            if not os.path.join(shardset.location, shard_basename)
            in [s.location for s in shardset.shards]
        ]

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for shard_index, shard_basename in enumerate(shard_basenames):
            shard_location = os.path.join(shardset.location, shard_basename)
            future = executor.submit(
                sync_shard_location,
                dataset_id=dataset_id,
                shardset_id=shardset_id,
                shard_location=shard_location,
                shard_index=shard_index,
            )
            futures.append(future)

        for future in as_completed(futures):
            shard = future.result()
            print(
                f"Shard {shard.index}/{len(shard_basenames)} ({shard.location}) created: {shard.id}"
            )

    return api.get_dataset(dataset_id)
