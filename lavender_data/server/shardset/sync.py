import os
from typing import Generator, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlmodel import update, insert, select

from lavender_data.logging import get_logger
from lavender_data.storage import list_files
from lavender_data.shard.inspect import OrphanShardInfo, inspect_shard
from lavender_data.shard.readers.exceptions import ReaderException
from lavender_data.server.background_worker import TaskStatus
from lavender_data.server.db import Shard, get_session
from lavender_data.server.distributed import get_cluster
from lavender_data.server.reader import get_reader_instance, ShardInfo
from lavender_data.server.cache import get_cache


def inspect_shardset_location(
    shardset_location: str,
    skip_locations: list[str] = [],
    num_workers: Optional[int] = None,
) -> Generator[tuple[OrphanShardInfo, int, int], None, None]:
    logger = get_logger(__name__)

    def _inspect_shard(shard_location: str, shard_index: int):
        return inspect_shard(shard_location), shard_index

    try:
        shard_index = 0

        shard_basenames = sorted(list_files(shardset_location))
        shard_locations: list[str] = []
        for shard_basename in shard_basenames:
            shard_location = os.path.join(shardset_location, shard_basename)
            if shard_location in skip_locations:
                shard_index += 1
                continue
            shard_locations.append(shard_location)

        with ThreadPoolExecutor(
            max_workers=num_workers or min(32, (os.cpu_count() or 1) + 4)
        ) as executor:
            futures = []
            for shard_location in shard_locations:
                future = executor.submit(
                    _inspect_shard,
                    shard_location=shard_location,
                    shard_index=shard_index,
                )
                shard_index += 1
                futures.append(future)

            for future in as_completed(futures):
                orphan_shard, current_shard_index = future.result()
                yield orphan_shard, current_shard_index, len(shard_locations)

    except ReaderException as e:
        logger.warning(f"Failed to inspect shardset {shardset_location}: {e}")
    except Exception as e:
        logger.exception(f"Error inspecting shardset {shardset_location}: {e}")


def sync_shardset_location(
    shardset_id: str,
    shardset_location: str,
    shardset_shard_locations: list[str],
    num_workers: Optional[int] = None,
    overwrite: bool = False,
) -> Generator[TaskStatus, None, None]:
    logger = get_logger(__name__)
    cluster = get_cluster()
    reader = get_reader_instance()

    yield TaskStatus(status="list", current=0, total=0)

    done_count = 0
    orphan_shard_infos: list[tuple[OrphanShardInfo, int]] = []
    for orphan_shard, shard_index, shard_count in inspect_shardset_location(
        shardset_location,
        skip_locations=[] if overwrite else shardset_shard_locations,
        num_workers=num_workers,
    ):
        done_count += 1
        orphan_shard_infos.append((orphan_shard, shard_index))
        yield TaskStatus(status="inspect", current=done_count, total=shard_count)

    orphan_shard_infos.sort(key=lambda x: x[1])

    yield TaskStatus(status="reflect", current=done_count, total=shard_count)

    session = next(get_session())
    for orphan_shard, shard_index in orphan_shard_infos:
        # TODO upsert https://github.com/fastapi/sqlmodel/issues/59
        updated = False
        if overwrite:
            result = session.exec(
                update(Shard)
                .where(
                    Shard.shardset_id == shardset_id,
                    Shard.index == shard_index,
                )
                .values(
                    location=orphan_shard.location,
                    filesize=orphan_shard.filesize,
                    samples=orphan_shard.samples,
                    format=orphan_shard.format,
                    statistics=orphan_shard.statistics,
                )
            )
            if result.rowcount > 0:
                updated = True

        if not updated:
            session.exec(
                insert(Shard).values(
                    shardset_id=shardset_id,
                    index=shard_index,
                    location=orphan_shard.location,
                    filesize=orphan_shard.filesize,
                    samples=orphan_shard.samples,
                    format=orphan_shard.format,
                    statistics=orphan_shard.statistics,
                )
            )

        reader.clear_cache(
            ShardInfo(
                shardset_id=shardset_id,
                index=shard_index,
                **orphan_shard.model_dump(),
            )
        )

    session.commit()

    cache = get_cache()
    cache.delete(f"dataset-statistics:{shardset_id}")

    shardset_shards = session.exec(
        select(Shard).where(Shard.shardset_id == shardset_id)
    ).all()
    if cluster is not None and cluster.is_head:
        try:
            logger.debug(
                f"Syncing shardset {shardset_id} to cluster nodes ({len(shardset_shards)} shards)"
            )
            cluster.sync_changes(shardset_shards)
        except Exception as e:
            logger.exception(e)

    yield TaskStatus(status="done", current=done_count, total=shard_count)
