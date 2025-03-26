import os
import tempfile
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from lavender_data.client import api
from lavender_data.storage import list_files

from .readers import Reader


def add_shard_to_dataset(
    dataset: api.DatasetPublic,
    shardset: Optional[api.ShardsetPublic],
    columns: Optional[dict[str, str]],
    shard_location: str,
    shard_index: int,
    overwrite: bool = False,
):
    shard_format = os.path.splitext(shard_location)[1].lstrip(".")

    with tempfile.NamedTemporaryFile() as f:
        reader = Reader.get(
            location=shard_location,
            format=shard_format,
            columns=columns,
            filepath=f.name,
            uid_column_name=dataset.uid_column_name,
            uid_column_type=None,
        )

        if columns is None:
            try:
                columns = reader.read_columns()
            except Exception:
                raise ValueError("Please specify columns for shardset.")

        if dataset.uid_column_name not in columns:
            raise ValueError(
                f'shardset must have uid column "{dataset.uid_column_name}" in columns'
            )

        if shardset is None:
            shardset = api.create_shardset(
                dataset_id=dataset.id,
                location=os.path.dirname(shard_location),
                columns=[
                    api.DatasetColumnOptions(
                        name=column_name,
                        type_=column_type,
                        description="",
                    )
                    for column_name, column_type in columns.items()
                ],
            )

        shard = api.create_shard(
            dataset_id=dataset.id,
            shardset_id=shardset.id,
            location=shard_location,
            filesize=os.path.getsize(f.name),
            samples=len(reader),
            format=shard_format,
            index=shard_index,
            overwrite=overwrite,
        )

    return shard, columns, shardset


def add_shards_to_dataset(
    dataset_id: str,
    location: str,
    shardset_id: Optional[str] = None,
    columns: Optional[dict[str, str]] = None,
    overwrite: bool = False,
    num_workers: int = 10,
) -> str:
    dataset = api.get_dataset(dataset_id)
    shard_basenames = list_files(location)
    shard_index = 0

    if shardset_id is not None:
        try:
            shardset = [s for s in dataset.shardsets if s.id == shardset_id].pop()
        except IndexError:
            raise ValueError(
                f"Shardset with id {shardset_id} not found on dataset {dataset_id}"
            )
    else:
        shard_basename = shard_basenames.pop()
        shard, columns, shardset = add_shard_to_dataset(
            dataset,
            None,
            columns,
            os.path.join(location, shard_basename),
            0,
            overwrite,
        )
        print(f"Shard 0/{len(shard_basenames)} ({shard_basename}) created: {shard.id}")
        shard_index += 1

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for shard_basename in shard_basenames:
            future = executor.submit(
                add_shard_to_dataset,
                dataset,
                shardset,
                columns,
                os.path.join(location, shard_basename),
                shard_index,
                overwrite,
            )
            futures.append(future)
            shard_index += 1

        for future in as_completed(futures):
            shard, _, _ = future.result()
            print(
                f"Shard {shard.index+1}/{len(shard_basenames)} ({shard.location}) created: {shard.id}"
            )

    return api.get_dataset(dataset_id)
