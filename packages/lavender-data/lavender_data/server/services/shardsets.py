import os
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel

from sqlmodel import select, update, insert

from lavender_data.logging import get_logger
from lavender_data.storage import list_files
from lavender_data.shard import inspect_shard
from lavender_data.shard.readers.exceptions import ReaderColumnsRequired
from lavender_data.server.cache import get_cache
from lavender_data.server.db import Shardset, Shard, get_session

logger = get_logger(__name__)


def get_main_shardset(shardsets: list[Shardset]) -> Shardset:
    """Pick the main shardset for getting samples from.
    During the iteration, the samples are yielded as the order of the samples in the main shardset.

    The main shardset is the one with the least samples.
    If there are multiple shardsets with the same number of samples,
    the one with the oldest creation date is picked.
    """
    shardset_with_least_samples = None
    total_samples = shardsets[0].total_samples
    for shardset in shardsets:
        if total_samples > shardset.total_samples:
            shardset_with_least_samples = shardset
            total_samples = shardset.total_samples
    if shardset_with_least_samples is not None:
        return shardset_with_least_samples

    oldest_shardset = shardsets[0]
    oldest_shardset_created_at = shardsets[0].created_at
    for shardset in shardsets:
        if oldest_shardset_created_at > shardset.created_at:
            oldest_shardset_created_at = shardset.created_at
            oldest_shardset = shardset

    return oldest_shardset


def span(index: int, shard_samples: list[int]) -> tuple[int, int]:
    sample_index = index
    shard_index = 0
    for samples in shard_samples:
        if sample_index < samples:
            break
        else:
            sample_index -= samples
            shard_index += 1

    return (shard_index, sample_index)


class SyncShardsetStatus(BaseModel):
    status: str
    done_count: int
    shard_count: int


def sync_shardset_location(
    shardset_id: str,
    shardset_location: str,
    shardset_shard_samples: list[int],
    shardset_shard_locations: list[str],
    num_workers: int = 10,
    overwrite: bool = False,
    cache_key: Optional[str] = None,
) -> str:
    def _inspect_shard(shard_location: str, shard_index: int):
        return inspect_shard(shard_location), shard_index

    if cache_key:
        cache = next(get_cache())
        status = SyncShardsetStatus(status="list_files", done_count=0, shard_count=0)
        cache.hset(cache_key, mapping=status.model_dump())
    else:
        cache = None
        status = None

    try:
        shard_basenames = sorted(list_files(shardset_location))
        shard_index = 0
        total_samples = 0

        if not overwrite:
            shard_basenames = [
                shard_basename
                for shard_basename in shard_basenames
                if os.path.join(shardset_location, shard_basename)
                not in shardset_shard_locations
            ]
            shard_index = len(shardset_shard_samples)
            total_samples = sum(shardset_shard_samples)

        session = next(get_session())
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for shard_basename in shard_basenames:
                shard_location = os.path.join(shardset_location, shard_basename)
                future = executor.submit(
                    _inspect_shard,
                    shard_location=shard_location,
                    shard_index=shard_index,
                )
                shard_index += 1
                futures.append(future)

            if cache:
                status.status = "inspecting"
                status.shard_count = shard_index
                cache.hset(cache_key, mapping=status.model_dump())

            for future in as_completed(futures):
                orphan_shard, current_shard_index = future.result()
                if cache:
                    status.done_count += 1
                    cache.hset(cache_key, mapping=status.model_dump())

                # TODO upsert https://github.com/fastapi/sqlmodel/issues/59
                updated = False
                if overwrite:
                    result = session.exec(
                        update(Shard)
                        .where(
                            Shard.shardset_id == shardset_id,
                            Shard.index == current_shard_index,
                        )
                        .values(
                            location=orphan_shard.location,
                            filesize=orphan_shard.filesize,
                            samples=orphan_shard.samples,
                            format=orphan_shard.format,
                        )
                    )
                    if result.rowcount > 0:
                        updated = True

                if not updated:
                    session.exec(
                        insert(Shard).values(
                            shardset_id=shardset_id,
                            location=orphan_shard.location,
                            filesize=orphan_shard.filesize,
                            samples=orphan_shard.samples,
                            format=orphan_shard.format,
                            index=current_shard_index,
                        )
                    )

                total_samples += orphan_shard.samples
                logger.info(
                    f"Shard {current_shard_index+1}/{shard_index} ({orphan_shard.location}) synced to {shardset_id}"
                )

        session.exec(
            update(Shardset)
            .where(Shardset.id == shardset_id)
            .values(
                shard_count=shard_index,
                total_samples=total_samples,
            )
        )
        session.commit()

        if cache:
            cache.delete(cache_key)

        return session.exec(select(Shardset).where(Shardset.id == shardset_id)).one()
    except ReaderColumnsRequired as e:
        logger.warning(
            f"Failed to sync shardset {shardset_id} at {shardset_location}: {e}"
        )
    except Exception as e:
        logger.exception(
            f"Error syncing shardset {shardset_id} at {shardset_location}: {e}"
        )
    finally:
        if cache_key and cache:
            cache.delete(cache_key)
