import contextlib
from urllib.parse import urlparse
import redis

from .abc import CacheInterface, PipelineInterface
from typing import Optional, Iterator, Union


class RedisCache(CacheInterface):
    def __init__(self, redis_url: str):
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

    def hget(self, name: str, key: str) -> Optional[str]:
        return self.redis.hget(name, key).decode("utf-8")

    def hgetall(self, name: str) -> dict:
        return self.redis.hgetall(name)

    def hdel(self, name: str, *keys: str) -> int:
        return self.redis.hdel(name, *keys)

    def lpush(self, name: str, *values: str) -> int:
        return self.redis.lpush(name, *values)

    def rpush(self, name: str, *values: str) -> int:
        return self.redis.rpush(name, *values)

    def lpop(self, name: str, count: Optional[int] = None) -> Optional[str]:
        return self.redis.lpop(name, count)

    def rpop(self, name: str) -> Optional[str]:
        return self.redis.rpop(name)

    def lrange(self, name: str, start: int, end: int) -> list[str]:
        return self.redis.lrange(name, start, end)

    def lindex(self, name: str, index: int) -> Optional[str]:
        return self.redis.lindex(name, index)

    @contextlib.contextmanager
    def lock(self, key: str, timeout: Optional[int] = None) -> Iterator[None]:
        with self.redis.lock(key, timeout=timeout):
            yield

    def ping(self) -> bool:
        return self.redis.ping()

    def close(self) -> None:
        self.redis.close()

    @contextlib.contextmanager
    def pipeline(self) -> Iterator[PipelineInterface]:
        pipe = self.redis.pipeline()
        try:
            yield pipe
        finally:
            return
