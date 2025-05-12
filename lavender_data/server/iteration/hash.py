import ujson as json
import hashlib
from typing import Optional

from lavender_data.server.cache import CacheClient
from lavender_data.server.db.models import Iteration


def _hash(o: object) -> str:
    return hashlib.sha256(
        json.dumps(o, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def get_iteration_hash(iteration: Iteration, dataset_id: Optional[str] = None) -> str:
    return _hash(
        {
            "dataset_id": dataset_id or iteration.dataset.id,
            "shardsets": [s.id for s in iteration.shardsets],
            "batch_size": iteration.batch_size,
            "filters": iteration.filters,
            "categorizer": iteration.categorizer,
            "collater": iteration.collater,
            "preprocessors": iteration.preprocessors,
            "shuffle": iteration.shuffle,
            "shuffle_seed": iteration.shuffle_seed,
            "shuffle_block_size": iteration.shuffle_block_size,
            "replication_pg": iteration.replication_pg,
        }
    )


def set_iteration_hash(
    iteration_id: str,
    iteration_hash: str,
    ttl: int,
    cache: CacheClient,
) -> None:
    cache.set(f"iteration_hash:{iteration_hash}", iteration_id, ex=ttl)


def get_iteration_id_from_hash(
    iteration_hash: str, cache: CacheClient
) -> Optional[str]:
    value = cache.get(f"iteration_hash:{iteration_hash}")
    if value is None:
        return None
    return value.decode("utf-8")
