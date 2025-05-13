import contextlib
from urllib.parse import urlparse

from .abc import CacheInterface, PipelineInterface
from typing import Optional, Iterator, Union


class RedisCache(CacheInterface):
    def __init__(self, redis_url: str):
        try:
            import redis
        except ImportError:
            raise ImportError(
                "Please install required dependencies for S3Storage. "
                "You can install them with `pip install lavender-data[redis]`"
            )

        url = urlparse(redis_url)
        self.redis = redis.StrictRedis(
            host=url.hostname,
            port=url.port,
            db=int(url.path.lstrip("/") or 0),
            username=url.username,
            password=url.password,
        )

    def set(self, key: str, value: Union[str, bytes], ex: Optional[int] = None) -> None:
        self.redis.set(key, value, ex=ex)

    def get(self, key: str) -> Optional[bytes]:
        return self.redis.get(key)

    def keys(self, pattern: str) -> list[str]:
        return self.redis.keys(pattern)

    def incr(self, key: str, amount: int = 1) -> int:
        return self.redis.incr(key, amount)

    def decr(self, key: str, amount: int = 1) -> int:
        return self.redis.decr(key, amount)

    def delete(self, key: str) -> None:
        self.redis.delete(key)

    def exists(self, key: str) -> bool:
        return self.redis.exists(key)

    def expire(self, key: str, seconds: int) -> bool:
        return self.redis.expire(key, seconds)

    def hset(
        self,
        name: str,
        key: Optional[str] = None,
        value: Optional[str] = None,
        mapping: Optional[dict] = None,
    ) -> int:
        return self.redis.hset(name, key=key, value=value, mapping=mapping)

    def hget(self, name: str, key: str) -> Optional[bytes]:
        return self.redis.hget(name, key)

    def hgetall(self, name: str) -> dict:
        return self.redis.hgetall(name)

    def hdel(self, name: str, *keys: str) -> int:
        return self.redis.hdel(name, *keys)

    def lpush(self, name: str, *values: str) -> int:
        return self.redis.lpush(name, *values)

    def rpush(self, name: str, *values: str) -> int:
        return self.redis.rpush(name, *values)

    def lpop(
        self, name: str, count: Optional[int] = None
    ) -> Optional[Union[bytes, list[bytes]]]:
        return self.redis.lpop(name, count)

    def rpop(self, name: str) -> Optional[bytes]:
        return self.redis.rpop(name)

    def lrange(self, name: str, start: int, end: int) -> list[bytes]:
        return self.redis.lrange(name, start, end)

    def lindex(self, name: str, index: int) -> Optional[bytes]:
        return self.redis.lindex(name, index)

    def llen(self, name: str) -> int:
        return self.redis.llen(name)

    def lrem(self, name: str, count: int, value: str) -> int:
        return self.redis.lrem(name, count, value)

    @contextlib.contextmanager
    def lock(self, key: str, timeout: Optional[int] = None) -> Iterator[None]:
        with self.redis.lock(key, timeout=timeout):
            yield

    @contextlib.contextmanager
    def pipeline(self) -> Iterator[PipelineInterface]:
        pipe = self.redis.pipeline()
        try:
            yield pipe
        finally:
            return
