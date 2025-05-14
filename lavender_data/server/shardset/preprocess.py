import os
import tempfile
import pyarrow as pa
import pyarrow.parquet as pq
from typing import Generator
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlmodel import select

from lavender_data.logging import get_logger
from lavender_data.storage import upload_file
from lavender_data.server.reader import GlobalSampleIndex, MainShardInfo, ShardInfo
from lavender_data.server.iteration import (
    process_next_samples,
    ProcessNextSamplesParams,
)
from lavender_data.server.background_worker.memory import TaskStatus, Memory
from lavender_data.server.db.models import (
    IterationCollater,
    IterationPreprocessor,
    Shardset,
)
from lavender_data.server.db import get_session

from .span import get_main_shardset

try:
    import torch
except ImportError:
    torch = None


def _decollate_batch(batch: dict) -> list[dict]:
    samples = []
    for key in batch.keys():
        values = batch[key]
        for i, value in enumerate(values):
            if len(samples) <= i:
                samples.append({})
            if torch is not None and isinstance(value, torch.Tensor):
                samples[i][key] = value.item()
            else:
                samples[i][key] = value
    return samples


def _export_shard(
    samples: list[dict],
    location: str,
) -> str:
    with tempfile.NamedTemporaryFile(suffix=".parquet") as f:
        table = pa.Table.from_pydict(
            {k: [s[k] for s in samples] for k in samples[0].keys()}
        )
        pq.write_table(table, f.name)
        upload_file(f.name, location)


def _generate_shardset(
    shardset_location: str,
    source_shardset_ids: list[str],
    uid_column_name: str,
    uid_column_type: str,
    # filters: list[IterationFilter],
    preprocessors: list[IterationPreprocessor],
    export_columns: list[str],
    batch_size: int,
    max_retry_count: int = 0,
    overwrite: bool = False,
) -> Generator[TaskStatus, None, None]:
    logger = get_logger(__name__)
    session = next(get_session())

    shardsets = session.exec(
        select(Shardset).where(Shardset.id.in_(source_shardset_ids))
    ).all()

    main_shardset = get_main_shardset(shardsets)
    feature_shardsets = [
        shardset for shardset in shardsets if shardset.id != main_shardset.id
    ]

    total = main_shardset.total_samples
    current = 0
    current_batch = 0
    _export_columns = export_columns + [uid_column_name]

    yield TaskStatus(status="", total=total, current=current)

    futures = []
    export_executor = ThreadPoolExecutor()

    for main_shard in main_shardset.shards:
        try:
            processed_samples = []

            feature_shards: list[ShardInfo] = []
            for shardset in feature_shardsets:
                feature_shard = next(
                    (s for s in shardset.shards if s.index == main_shard.index), None
                )
                if feature_shard is None:
                    raise ValueError(
                        f"Shard {main_shard.index} of main shardset {main_shardset.id} has no corresponding shard in {shardset.id}"
                    )
                feature_shards.append(
                    ShardInfo(
                        shardset_id=feature_shard.shardset_id,
                        index=feature_shard.index,
                        samples=feature_shard.samples,
                        location=feature_shard.location,
                        format=feature_shard.format,
                        filesize=feature_shard.filesize,
                        columns={c.name: c.type for c in shardset.columns},
                    )
                )

            for sample_index in range(main_shard.samples):
                indices = []

                indices.append(
                    GlobalSampleIndex(
                        index=current,
                        uid_column_name=uid_column_name,
                        uid_column_type=uid_column_type,
                        main_shard=MainShardInfo(
                            sample_index=sample_index,
                            shardset_id=main_shardset.id,
                            index=main_shard.index,
                            samples=main_shard.samples,
                            location=main_shard.location,
                            format=main_shard.format,
                            filesize=main_shard.filesize,
                            columns={c.name: c.type for c in main_shardset.columns},
                        ),
                        feature_shards=feature_shards,
                    )
                )
                current += 1

                if len(indices) < batch_size:
                    continue

                params = ProcessNextSamplesParams(
                    current=current_batch,
                    global_sample_indices=indices,
                    collater=IterationCollater(name="default", params={}),
                    preprocessors=preprocessors,
                    batch_size=batch_size,
                )
                current_batch += 1
                indices = []

                try:
                    batch = process_next_samples(
                        params, max_retry_count=max_retry_count
                    )
                    keys = list(batch.keys())
                    for key in keys:
                        if key not in _export_columns:
                            del batch[key]

                    processed_samples.extend(_decollate_batch(batch))
                except Exception as e:
                    logger.exception(
                        f"Error processing sample {sample_index} of shard {main_shard.index} of main shardset {main_shardset.id}: {e}"
                    )
                    continue

                yield TaskStatus(status="processing", total=total, current=current)

            location = os.path.join(
                shardset_location, f"shard.{main_shard.index:05d}.parquet"
            )
            logger.info(
                f"Exporting generated shard {main_shard.index} to {location} ({len(processed_samples)} samples)"
            )
            future = export_executor.submit(
                _export_shard,
                samples=processed_samples,
                location=location,
            )
            futures.append(future)
        except Exception as e:
            logger.exception(
                f"Error processing shard {main_shard.index} of main shardset {main_shardset.id}: {e}"
            )
            continue

    yield TaskStatus(
        status="waiting for export to complete", total=total, current=current
    )
    for future in as_completed(futures):
        try:
            future.result()
        except Exception as e:
            logger.exception(f"Error exporting shard: {e}")

    export_executor.shutdown(wait=True)
    logger.info("Export complete")


def preprocess_dataset_task(
    shardset_location: str,
    source_shardset_ids: list[str],
    uid_column_name: str,
    uid_column_type: str,
    preprocessors: list[IterationPreprocessor],
    export_columns: list[str],
    batch_size: int,
    overwrite: bool = False,
    *,
    memory: Memory,
    task_uid: str,
):
    for status in _generate_shardset(
        shardset_location,
        source_shardset_ids,
        uid_column_name,
        uid_column_type,
        preprocessors,
        export_columns,
        batch_size,
        overwrite,
    ):
        memory.set_task_status(
            task_uid,
            status=status.status,
            total=status.total,
            current=status.current,
        )
