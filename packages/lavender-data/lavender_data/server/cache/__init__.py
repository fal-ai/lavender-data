from urllib.parse import urlparse
from typing import Annotated, Optional

import redis
from fastapi import Depends

from lavender_data.logging import get_logger

redis_client = None


def setup_redis(redis_url: Optional[str] = None):
    global redis_client

    if not redis_url:
        get_logger(__name__).warning(
            "LAVENDER_DATA_REDIS_URL is not set, using redis://localhost:6379/0"
        )
        redis_url = "redis://localhost:6379/0"

    url = urlparse(redis_url)

    redis_client = redis.StrictRedis(
        host=url.hostname,
        port=url.port,
        db=int(url.path.lstrip("/") or 0),
        username=url.username,
        password=url.password,
    )


def get_client():
    if not redis_client:
        raise RuntimeError("Redis client not initialized")

    yield redis_client


RedisClient = Annotated[redis.Redis, Depends(get_client)]


def register_worker():
    rank = redis_client.incr("lavender_data_worker_rank", 1) - 1
    return rank


def deregister_worker():
    redis_client.decr("lavender_data_worker_rank", 1)
