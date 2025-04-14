from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Optional, Iterator, Any, Union


class CacheOperations(ABC):
    @abstractmethod
    def set(
        self, key: str, value: Union[str, bytes], ex: Optional[int] = None
    ) -> None: ...

    @abstractmethod
    def get(self, key: str) -> Optional[bytes]: ...

    @abstractmethod
    def keys(self, pattern: str) -> list[str]: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def expire(self, key: str, seconds: int) -> bool: ...

    @abstractmethod
    def incr(self, key: str, amount: int = 1) -> int: ...

    @abstractmethod
    def decr(self, key: str, amount: int = 1) -> int: ...

    @abstractmethod
    def hset(
        self,
        name: str,
        key: Optional[str] = None,
        value: Optional[str] = None,
        mapping: Optional[dict] = None,
    ) -> int: ...

    @abstractmethod
    def hget(self, name: str, key: str) -> Optional[str]: ...

    @abstractmethod
    def hgetall(self, name: str) -> dict: ...

    @abstractmethod
    def hdel(self, name: str, *keys: str) -> int: ...

    @abstractmethod
    def lpush(self, name: str, *values: str) -> int: ...

    @abstractmethod
    def rpush(self, name: str, *values: str) -> int: ...

    @abstractmethod
    def lpop(self, name: str, count: Optional[int] = None) -> Optional[str]: ...

    @abstractmethod
    def rpop(self, name: str) -> Optional[str]: ...

    @abstractmethod
    def lrange(self, name: str, start: int, end: int) -> list[str]: ...

    @abstractmethod
    def lindex(self, name: str, index: int) -> Optional[str]: ...


class CacheInterface(CacheOperations):
    @abstractmethod
    def lock(self, key: str, timeout: Optional[int] = None) -> Iterator[None]: ...

    @contextmanager
    @abstractmethod
    def pipeline(self) -> Iterator["PipelineInterface"]: ...


class PipelineInterface(CacheOperations):
    @abstractmethod
    def execute(self) -> list[Any]: ...
