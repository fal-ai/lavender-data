from lavender_data.server.shardset import sync_shardset_location
from lavender_data.logging import get_logger

from lavender_data.server.background_worker.memory import Memory


def sync_shardset_location_task(
    shardset_id: str,
    shardset_location: str,
    shardset_shard_samples: list[int],
    shardset_shard_locations: list[str],
    dataset_id: str,
    num_workers: int,
    overwrite: bool,
    cache_key: str,
    *,
    memory: Memory,
):
    logger = get_logger(__name__)
    try:
        for status in sync_shardset_location(
            shardset_id,
            shardset_location,
            shardset_shard_samples,
            shardset_shard_locations,
            dataset_id,
            num_workers,
            overwrite,
        ):
            memory.set(cache_key, status.model_dump_json())
        memory.set(cache_key, status.model_dump_json(), ex=10)
    except Exception as e:
        logger.exception(e)
        memory.set(cache_key, f"error:{e}", ex=10)
