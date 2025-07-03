import os
import json
from typing import Generator, Optional

from sqlmodel import update, insert, select, delete

from lavender_data.logging import get_logger
from lavender_data.storage import list_files
from lavender_data.shard.inspect import OrphanShardInfo, inspect_shard
from lavender_data.shard.readers.exceptions import ReaderException
from lavender_data.server.background_worker import (
    TaskStatus,
    get_background_worker,
    pool_task,
)
from lavender_data.server.db.models import Shard, Shardset, ShardStatistics
from lavender_data.server.db import db_manual_session
from lavender_data.server.distributed import get_cluster
from lavender_data.server.dataset.statistics import get_dataset_statistics
from lavender_data.server.reader import get_reader_instance, ShardInfo
from lavender_data.server.cache import get_cache


@pool_task()
def inspect_shard_task(
    shard_location: str,
    shard_index: int,
    statistics_types: dict[str, str],
    known_columns: Optional[dict[str, str]] = None,
):
    return inspect_shard(shard_location, statistics_types, known_columns), shard_index


def inspect_shardset_location(
    shardset_location: str,
    skip_locations: list[str] = [],
    shardset_columns: Optional[dict[str, str]] = None,
) -> Generator[tuple[OrphanShardInfo, int, int], None, None]:
    logger = get_logger(__name__)
    pool = get_background_worker().process_pool()
    work_ids = []

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
        total_shards = len(shard_locations)

        if total_shards == 0:
            yield None, shard_index, total_shards
            return

        first_shard_location = os.path.join(shardset_location, shard_basenames[0])
        first_shard = inspect_shard(
            first_shard_location,
            known_columns=shardset_columns,
        )
        statistics_types = {
            column_name: s["type"] for column_name, s in first_shard.statistics.items()
        }

        if first_shard_location in shard_locations:
            yield first_shard, shard_index, total_shards
            shard_locations.remove(first_shard_location)
            shard_index += 1

        for shard_location in shard_locations:
            work_ids.append(
                pool.submit(
                    inspect_shard_task,
                    shard_location=shard_location,
                    shard_index=shard_index,
                    statistics_types=statistics_types,
                    known_columns=shardset_columns,
                )
            )
            shard_index += 1

        for orphan_shard, current_shard_index in pool.as_completed(
            work_ids, timeout=3 * 60 * 60
        ):
            yield orphan_shard, current_shard_index, total_shards

    except ReaderException as e:
        logger.warning(f"Failed to inspect shardset {shardset_location}: {e}")
    except Exception as e:
        logger.exception(f"Error inspecting shardset {shardset_location}: {e}")
    finally:
        pool.cancel(*work_ids)


def sync_shardset_location(
    shardset_id: str,
    shardset_location: str,
    shardset_shard_locations: list[str],
    shardset_columns: dict[str, str],
    overwrite: bool = False,
) -> Generator[TaskStatus, None, None]:
    # TODO handle when columns are changed
    logger = get_logger(__name__)
    try:
        cluster = get_cluster()
        reader = get_reader_instance()

        yield TaskStatus(status="list", current=0, total=0)

        shard_count = 0
        done_count = 0
        for orphan_shard, shard_index, shard_count in inspect_shardset_location(
            shardset_location,
            skip_locations=[] if overwrite else shardset_shard_locations,
            shardset_columns=None if len(shardset_columns) == 0 else shardset_columns,
        ):
            if shard_count == 0:
                return

            logger.debug(
                f"Inspected shard {orphan_shard.location} ({done_count}/{shard_count})"
            )

            with db_manual_session() as session:
                updated = False
                # TODO upsert https://github.com/fastapi/sqlmodel/issues/59
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
                        )
                    )

                shard = session.exec(
                    select(Shard).where(
                        Shard.shardset_id == shardset_id,
                        Shard.index == shard_index,
                    )
                ).one_or_none()

                if shard is None:
                    logger.warning(
                        f"Shard {shard_index} not created in shardset {shardset_id}"
                    )
                    continue

                updated = False
                result = session.exec(
                    update(ShardStatistics)
                    .where(ShardStatistics.shard_id == shard.id)
                    .values(data=orphan_shard.statistics)
                )
                if result.rowcount > 0:
                    updated = True

                if not updated:
                    session.exec(
                        insert(ShardStatistics).values(
                            shard_id=shard.id,
                            data=orphan_shard.statistics,
                        )
                    )

                session.commit()

            reader.clear_cache(
                ShardInfo(
                    shardset_id=shardset_id,
                    index=shard_index,
                    **orphan_shard.model_dump(),
                )
            )
            done_count += 1
            yield TaskStatus(status="inspect", current=done_count, total=shard_count)

        yield TaskStatus(status="reflect", current=done_count, total=shard_count)

        with db_manual_session() as session:
            result = session.exec(
                delete(Shard).where(
                    Shard.shardset_id == shardset_id,
                    Shard.index
                    >= (
                        shard_count
                        if overwrite
                        else shard_count + len(shardset_shard_locations)
                    ),
                )
            )
            logger.debug(
                f"Deleted {result.rowcount} shards from shardset {shardset_id}"
            )
            session.commit()

        with db_manual_session() as session:
            shardset = session.exec(
                select(Shardset).where(Shardset.id == shardset_id)
            ).first()
            dataset_id = shardset.dataset_id

        dataset_statistics = get_dataset_statistics(dataset_id)

        cache = next(get_cache())
        cache.set(f"dataset-statistics:{dataset_id}", json.dumps(dataset_statistics))
        cache.delete(f"preview:{dataset_id}")

        if cluster is not None and cluster.is_head:
            try:
                with db_manual_session() as session:
                    shardset_shards = session.exec(
                        select(Shard).where(Shard.shardset_id == shardset_id)
                    ).all()
                logger.debug(
                    f"Syncing shardset {shardset_id} to cluster nodes ({len(shardset_shards)} shards)"
                )
                cluster.sync_changes(shardset_shards)
            except Exception as e:
                logger.exception(e)
    except GeneratorExit:
        logger.info(f"Sync shardset {shardset_id} aborted")
