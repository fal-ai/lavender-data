from typing import Annotated, Optional

from fastapi import Depends

from lavender_data.logging import get_logger

from .abc import CacheInterface
from .redis import RedisCache
from .inmemory import InMemoryCache

cache_client: CacheInterface = None


def setup_cache(redis_url: Optional[str] = None):
    global cache_client

    if redis_url:
        cache_client = RedisCache(redis_url)
    else:
        get_logger(__name__).warning(
            "LAVENDER_DATA_REDIS_URL is not set, using in memory cache"
        )
        cache_client = InMemoryCache()


def get_cache():
    if not cache_client:
        raise RuntimeError("Redis client not initialized")

    yield cache_client


CacheClient = Annotated[CacheInterface, Depends(get_cache)]


def register_worker():
    rank = cache_client.incr("lavender_data_worker_rank", 1) - 1
    return rank


def deregister_worker():
    cache_client.decr("lavender_data_worker_rank", 1)
