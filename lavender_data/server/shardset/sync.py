import os
from typing import Generator
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlmodel import update, insert, select

from lavender_data.server.background_worker.memory import Memory, TaskStatus
from lavender_data.logging import get_logger
from lavender_data.storage import list_files
from lavender_data.shard.inspect import OrphanShardInfo, inspect_shard
from lavender_data.shard.readers.exceptions import ReaderException
from lavender_data.server.db import Shardset, Shard, get_session


def inspect_shardset_location(
    shardset_location: str,
    skip_basenames: list[str] = [],
    num_workers: int = 10,
) -> Generator[tuple[OrphanShardInfo, int, int], None, None]:
    logger = get_logger(__name__)

    def _inspect_shard(shard_location: str, shard_index: int):
        return inspect_shard(shard_location), shard_index

    shard_index = 0

    try:
        shard_basenames = sorted(list_files(shardset_location))

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for shard_basename in shard_basenames:
                if shard_basename in skip_basenames:
                    continue
                shard_location = os.path.join(shardset_location, shard_basename)
                future = executor.submit(
                    _inspect_shard,
                    shard_location=shard_location,
                    shard_index=shard_index,
                )
                shard_index += 1
                futures.append(future)

            for future in as_completed(futures):
                orphan_shard, current_shard_index = future.result()
                yield orphan_shard, current_shard_index, len(shard_basenames)

    except ReaderException as e:
        logger.warning(f"Failed to inspect shardset {shardset_location}: {e}")
    except Exception as e:
        logger.exception(f"Error inspecting shardset {shardset_location}: {e}")


def sync_shardset_location(
    shardset_id: str,
    shardset_location: str,
    shardset_shard_samples: list[int],
    shardset_shard_locations: list[str],
    num_workers: int = 10,
    overwrite: bool = False,
) -> Generator[TaskStatus, None, None]:
    # TODO di?
    logger = get_logger(__name__)
    session = next(get_session())

    yield TaskStatus(status="list", current=0, total=0)

    done_count = 0
    shard_and_index: list[tuple[OrphanShardInfo, int]] = []
    for orphan_shard, current_shard_index, shard_count in inspect_shardset_location(
        shardset_location,
        skip_basenames=[] if overwrite else shardset_shard_locations,
        num_workers=num_workers,
    ):
        done_count += 1
        shard_and_index.append((orphan_shard, current_shard_index))
        yield TaskStatus(status="inspect", current=done_count, total=shard_count)

    shard_and_index.sort(key=lambda x: x[1])
    shard_infos = [x[0] for x in shard_and_index]

    if overwrite:
        shard_index = 0
        total_samples = 0
    else:
        shard_index = len(shardset_shard_samples)
        total_samples = sum(shardset_shard_samples)

    yield TaskStatus(status="reflect", current=done_count, total=shard_count)

    current_shard_index = shard_index
    for orphan_shard in shard_infos:
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

        current_shard_index += 1
        total_samples += orphan_shard.samples
        logger.info(
            f"Shard {current_shard_index}/{shard_index+len(shard_infos)} ({orphan_shard.location}) synced to {shardset_id}"
        )

    session.exec(
        update(Shardset)
        .where(Shardset.id == shardset_id)
        .values(
            shard_count=current_shard_index,
            total_samples=total_samples,
        )
    )
    session.commit()

    yield TaskStatus(status="done", current=done_count, total=shard_count)


def sync_shardset_location_task(
    shardset_id: str,
    shardset_location: str,
    shardset_shard_samples: list[int],
    shardset_shard_locations: list[str],
    num_workers: int,
    overwrite: bool,
    *,
    memory: Memory,
    task_uid: str,
):
    logger = get_logger(__name__)
    try:
        memory.set_task_status(task_uid, status="", current=0, total=0)
        for status in sync_shardset_location(
            shardset_id,
            shardset_location,
            shardset_shard_samples,
            shardset_shard_locations,
            num_workers,
            overwrite,
        ):
            memory.set_task_status(
                task_uid,
                status=status.status,
                current=status.current,
                total=status.total,
            )
    except Exception as e:
        logger.exception(e)

    session = next(get_session())
    shardset = session.exec(select(Shardset).where(Shardset.id == shardset_id)).one()
    return shardset, shardset.shards
