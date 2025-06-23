import os
import time
from typing import Any, Union

from sqlmodel import select
from sqlalchemy.orm import selectinload, load_only

import filetype
import hashlib
import numpy as np
import json

from lavender_data.server.settings import files_dir
from lavender_data.server.db import db_manual_session
from lavender_data.server.db.models import Dataset, Shard, Shardset
from lavender_data.server.cache import CacheClient, get_cache
from lavender_data.server.reader import (
    get_reader_instance,
    ReaderInstance,
    GlobalSampleIndex,
    ShardInfo,
    MainShardInfo,
)
from lavender_data.server.shardset import get_main_shardset, span
from lavender_data.storage import get_url
from lavender_data.serialize import serialize_list
from lavender_data.logging import get_logger

try:
    import torch
except ImportError:
    torch = None


def _read_dataset(
    dataset_id: str,
    index: int,
    reader: ReaderInstance,
    cache: CacheClient,
) -> GlobalSampleIndex:
    with db_manual_session() as session:
        dataset: Dataset = session.exec(
            select(Dataset)
            .where(Dataset.id == dataset_id)
            .options(
                selectinload(Dataset.shardsets).options(
                    selectinload(Shardset.columns),
                    selectinload(Shardset.shards).options(
                        load_only(
                            Shard.id,
                            Shard.shardset_id,
                            Shard.location,
                            Shard.filesize,
                            Shard.samples,
                            Shard.index,
                            Shard.format,
                            Shard.created_at,
                        )
                    ),
                )
            )
        ).one()

    if dataset is None:
        raise ValueError(f"Dataset {dataset_id} not found")

    main_shardset = get_main_shardset(dataset.shardsets)

    if cache.exists(f"preview-shards:{main_shardset.id}"):
        shard_samples = json.loads(cache.get(f"preview-shards:{main_shardset.id}"))
    else:
        shard_samples = [
            shard.samples
            for shard in sorted(main_shardset.shards, key=lambda s: s.index)
        ]
        cache.set(
            f"preview-shards:{main_shardset.id}",
            json.dumps(shard_samples),
            ex=3 * 60,
        )

    shard_index, sample_index = span(index, shard_samples)

    main_shard = None
    uid_column_type = None
    feature_shards = []
    for shardset in dataset.shardsets:
        columns = {column.name: column.type for column in shardset.columns}
        if dataset.uid_column_name in columns:
            uid_column_type = columns[dataset.uid_column_name]

        if cache.exists(f"preview-shards:{shardset.id}:{shard_index}"):
            shard = Shard.model_validate_json(
                cache.get(f"preview-shards:{shardset.id}:{shard_index}")
            )
        else:
            try:
                shard = next(
                    (shard for shard in shardset.shards if shard.index == shard_index)
                )
            except StopIteration:
                # f"Shard index {shard_index} not found in shardset {shardset.id}",
                continue
            cache.set(
                f"preview-shards:{shardset.id}:{shard_index}",
                shard.model_dump_json(),
                ex=3 * 60,
            )

        shard_info = ShardInfo(
            shardset_id=shardset.id,
            index=shard.index,
            samples=shard.samples,
            location=shard.location,
            format=shard.format,
            filesize=shard.filesize,
            columns=columns,
        )
        if shardset.id == main_shardset.id:
            main_shard = MainShardInfo(
                **shard_info.model_dump(), sample_index=sample_index
            )
        else:
            feature_shards.append(shard_info)

    if uid_column_type is None:
        raise ValueError("Dataset has no uid column")

    if main_shard is None:
        raise ValueError("Dataset has no shards")

    return reader.get_sample(
        GlobalSampleIndex(
            index=index,
            uid_column_name=dataset.uid_column_name,
            uid_column_type=uid_column_type,
            main_shard=main_shard,
            feature_shards=feature_shards,
        )
    )


def _get_extension(obj: Union[str, bytes, bytearray]) -> str:
    kind = filetype.guess(obj)
    if kind is None:
        raise ValueError(f"Failed to guess file type of {obj}")
    return kind.extension


def _set_file(content: bytes):
    _hash = hashlib.md5(content).hexdigest()
    filename = _hash + "." + _get_extension(content)
    local_path = os.path.join(files_dir, filename)
    with open(local_path, "wb") as f:
        f.write(content)
    return filename


def refine_sample_previewable(sample: dict[str, Any]):
    for key in sample.keys():
        if type(sample[key]) == bytes:
            if len(sample[key]) > 0:
                local_path = _set_file(sample[key])
                sample[key] = f"file://{local_path}"
                # sample[key] = "<bytes>"
            else:
                sample[key] = ""
        if type(sample[key]) == dict:
            if sample[key].get("bytes"):
                local_path = _set_file(sample[key]["bytes"])
                sample[key] = f"file://{local_path}"
            else:
                sample[key] = str(sample[key])
        if type(sample[key]) == str:
            if any(
                sample[key].startswith(prefix)
                for prefix in ["s3://", "hf://", "http://", "https://"]
            ):
                sample[key] = get_url(sample[key])
        if torch and isinstance(sample[key], torch.Tensor):
            sample[key] = (
                f"<torch.Tensor shape={sample[key].shape} dtype={sample[key].dtype}>"
            )
        if isinstance(sample[key], np.ndarray):
            sample[key] = (
                f"<numpy.ndarray shape={sample[key].shape} dtype={sample[key].dtype}>"
            )
    return sample


def preview_dataset(
    dataset_id: str,
    offset: int,
    limit: int,
) -> list[dict[str, Any]]:
    cache = next(get_cache())
    reader = get_reader_instance()

    samples = []
    for index in range(offset, offset + limit):
        try:
            sample = _read_dataset(dataset_id, index, reader, cache)
        except IndexError:
            break

        sample = refine_sample_previewable(sample)
        samples.append(sample)

    return samples


def preview_dataset_task(
    preview_id: str,
    dataset_id: str,
    offset: int,
    limit: int,
) -> list[dict[str, Any]]:
    cache = next(get_cache())
    logger = get_logger(__name__)
    logger.info(f"Previewing dataset {dataset_id} {offset}-{offset+limit-1}")
    start_time = time.time()
    try:
        samples = preview_dataset(dataset_id, offset, limit)
        # cache for 60 minutes
        cache.hset(f"preview:{dataset_id}", preview_id, serialize_list(samples))
    except Exception as e:
        logger.exception(f"Failed to preview dataset {dataset_id}: {e}")
        cache.set(f"preview:{dataset_id}:{preview_id}:error", str(e), ex=3 * 60)
        raise e
    end_time = time.time()
    logger.info(
        f"Previewed dataset {dataset_id} {offset}-{offset+limit-1} in {end_time - start_time:.2f}s"
    )
    return samples
