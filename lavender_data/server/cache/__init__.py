from typing import Annotated, Optional, Any

from fastapi import Depends

from lavender_data.logging import get_logger

from .abc import CacheInterface
from .redis import RedisCache
from .inmemory import InMemoryCache

cache_client: CacheInterface = None


def setup_cache(redis_url: Optional[str] = None):
    global cache_client

    if redis_url:
        get_logger(__name__).debug("Using redis cache")
        cache_client = RedisCache(redis_url=redis_url)
    else:
        get_logger(__name__).debug("Using inmemory cache")
        cache_client = InMemoryCache()


def get_cache():
    if not cache_client:
        raise RuntimeError("Redis client not initialized")

    yield cache_client


CacheClient = Annotated[CacheInterface, Depends(get_cache)]
