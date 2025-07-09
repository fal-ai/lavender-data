import os
import time
from typing import Any, Union

from sqlmodel import select
from sqlalchemy.orm import selectinload

import filetype
import hashlib
import numpy as np
import json

from lavender_data.server.settings import files_dir
from lavender_data.server.db import db_manual_session
from lavender_data.server.db.models import (
    Dataset,
    Shard,
    Shardset,
    DatasetPublic,
    ShardPublic,
    ShardsetPublic,
    DatasetColumnPublic,
)
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


class _Shardset(ShardsetPublic):
    shards: list[ShardPublic]
    columns: list[DatasetColumnPublic]


class _Dataset(DatasetPublic):
    shardsets: list[_Shardset]


def _read_dataset(
    dataset: _Dataset,
    index: int,
    reader: ReaderInstance,
    cache: CacheClient,
) -> GlobalSampleIndex:
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
        ),
        join="left",
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


def refine_value_previewable(value: Any):
    if type(value) == bytes:
        if len(value) > 0:
            try:
                local_path = _set_file(value)
                return f"file://{local_path}"
            except ValueError:
                return f"<bytes>"
        else:
            return ""
    elif type(value) == dict:
        if value.get("bytes"):
            try:
                local_path = _set_file(value["bytes"])
                return f"file://{local_path}"
            except ValueError:
                return str(value)
        else:
            return str(value)
    elif type(value) == str:
        if any(
            value.startswith(prefix)
            for prefix in ["s3://", "hf://", "http://", "https://"]
        ):
            return get_url(value)
    elif torch and isinstance(value, torch.Tensor):
        return f"<torch.Tensor shape={value.shape} dtype={value.dtype}>"
    elif isinstance(value, np.ndarray):
        return f"<numpy.ndarray shape={value.shape} dtype={value.dtype}>"

    return value


def refine_sample_previewable(sample: dict[str, Any]):
    for key in sample.keys():
        sample[key] = refine_value_previewable(sample[key])
    return sample


def preview_dataset(
    dataset_id: str,
    offset: int,
    limit: int,
) -> list[dict[str, Any]]:
    cache = next(get_cache())
    reader = get_reader_instance()

    cached_dataset = cache.hget(f"preview:{dataset_id}", "dataset")
    if cached_dataset is None:
        with db_manual_session() as session:
            dataset = session.exec(
                select(Dataset)
                .where(Dataset.id == dataset_id)
                .options(
                    selectinload(Dataset.shardsets).options(
                        selectinload(Shardset.columns),
                        selectinload(Shardset.shards),
                    )
                )
            ).one()

        if dataset is None:
            raise ValueError(f"Dataset {dataset_id} not found")

        dataset = _Dataset.model_validate(dataset)
        cache.hset(f"preview:{dataset_id}", "dataset", dataset.model_dump_json())
        for shardset in dataset.shardsets:
            cache.hset(
                f"preview:{dataset_id}",
                f"dataset.shardsets.{shardset.id}",
                shardset.model_dump_json(),
            )
    else:
        dataset = _Dataset.model_validate_json(cached_dataset)

    samples = []
    for index in range(offset, offset + limit):
        try:
            sample = _read_dataset(dataset, index, reader, cache)
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
