import time
import threading
from typing import Optional, Any, Iterator, Union
from contextlib import contextmanager
from fnmatch import fnmatch
from .abc import CacheInterface, CacheOperations


class InMemoryCache(CacheInterface):
    """
    An in-memory implementation of Redis client with basic Redis functionality.
    Designed to be API-compatible with redis.StrictRedis for common operations.
    """

    def __init__(self):
        # Main storage dict - mimics Redis key-value store
        self._data: dict[str, Any] = {}
        # For expiring keys
        self._expiry: dict[str, float] = {}
        # For hash maps
        self._hash_data: dict[str, dict[str, str]] = {}
        # For lists
        self._list_data: dict[str, list[str]] = {}
        # For locks
        self._lock_data: dict[str, threading.Lock] = {}
        # Lock for thread safety
        self._lock = threading.RLock()
        # Start expiry checker thread
        self._start_expiry_thread()

    def _start_expiry_thread(self):
        """Start a background thread to check for expired keys"""

        def check_expiry():
            while True:
                with self._lock:
                    now = time.time()
                    expired_keys = [k for k, exp in self._expiry.items() if exp <= now]
                    for key in expired_keys:
                        self.delete(key)
                time.sleep(1)  # Check every second

        thread = threading.Thread(target=check_expiry, daemon=True)
        thread.start()

    def _check_expiry(self, key):
        """Check if a key has expired and remove it if needed"""
        if key in self._expiry and self._expiry[key] <= time.time():
            self.delete(key)
            return True
        return False

    def _ensure_bytes(self, value: Union[str, bytes]) -> bytes:
        if isinstance(value, str):
            return value.encode("utf-8")
        return value

    # Basic key operations
    def set(
        self,
        key: str,
        value: Union[str, bytes],
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Set key to value with optional expiration"""
        with self._lock:
            if nx and key in self._data:
                return False
            if xx and key not in self._data:
                return False

            value = self._ensure_bytes(value)

            self._data[key] = value

            # Handle expiration
            if ex:  # seconds
                self._expiry[key] = time.time() + ex
            elif px:  # milliseconds
                self._expiry[key] = time.time() + (px / 1000)

            return True

    def get(self, key: str) -> Optional[bytes]:
        """Get the value of key"""
        with self._lock:
            if self._check_expiry(key):
                return None
            return self._data.get(key)

    def keys(self, pattern: str) -> list[str]:
        """Get all keys matching the pattern"""
        with self._lock:
            return [k for k in self._data if fnmatch(k, pattern)]

    def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        deleted = 0
        with self._lock:
            for key in keys:
                # Remove from all storage types
                if key in self._data:
                    del self._data[key]
                    deleted += 1
                if key in self._hash_data:
                    del self._hash_data[key]
                    deleted += 1
                if key in self._list_data:
                    del self._list_data[key]
                    deleted += 1
                if key in self._expiry:
                    del self._expiry[key]
        return deleted

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        with self._lock:
            if self._check_expiry(key):
                return False
            return key in self._data or key in self._hash_data or key in self._list_data

    def expire(self, key: str, seconds: int) -> bool:
        """Set a key's time to live in seconds"""
        with self._lock:
            if not self.exists(key):
                return False
            self._expiry[key] = time.time() + seconds
            return True

    def incr(self, key: str, amount: int = 1) -> int:
        """Increment the value of key by amount"""
        with self._lock:
            if not self.exists(key):
                self._data[key] = amount
            else:
                self._data[key] += amount

            return self._data[key]

    def decr(self, key: str, amount: int = 1) -> int:
        """Decrement the value of key by amount"""
        with self._lock:
            if not self.exists(key):
                self._data[key] = -amount
            else:
                self._data[key] -= amount

            return self._data[key]

    # Hash operations
    def hset(
        self,
        name: str,
        key: Optional[str] = None,
        value: Optional[str] = None,
        mapping: Optional[dict] = None,
    ) -> int:
        """Set key to value within hash name"""
        with self._lock:
            if name not in self._hash_data:
                self._hash_data[name] = {}

            if mapping:
                for k, v in mapping.items():
                    v = self._ensure_bytes(v)
                    self._hash_data[name][k] = v
                return len(mapping)
            elif key is not None and value is not None:
                is_new = key not in self._hash_data[name]
                value = self._ensure_bytes(value)
                self._hash_data[name][key] = value
                return 1 if is_new else 0
            else:
                return 0

    def hget(self, name: str, key: str) -> Optional[str]:
        """Get the value of key within the hash name"""
        with self._lock:
            if self._check_expiry(name):
                return None
            if name not in self._hash_data:
                return None
            return self._hash_data[name].get(key)

    def hgetall(self, name: str) -> dict[str, str]:
        """Get all the fields and values in a hash"""
        with self._lock:
            if self._check_expiry(name):
                return {}
            return self._hash_data.get(name, {}).copy()

    def hdel(self, name: str, *keys: str) -> int:
        """Delete one or more hash fields"""
        with self._lock:
            if name not in self._hash_data:
                return 0

            deleted = 0
            for key in keys:
                if key in self._hash_data[name]:
                    del self._hash_data[name][key]
                    deleted += 1

            # Clean up empty hash
            if not self._hash_data[name]:
                del self._hash_data[name]

            return deleted

    # List operations
    def lpush(self, name: str, *values: str) -> int:
        """Push values onto the head of the list name"""
        with self._lock:
            if name not in self._list_data:
                self._list_data[name] = []

            for value in values:
                self._list_data[name].insert(0, self._ensure_bytes(value))

            return len(self._list_data[name])

    def rpush(self, name: str, *values: str) -> int:
        """Push values onto the tail of the list name"""
        with self._lock:
            if name not in self._list_data:
                self._list_data[name] = []

            for value in values:
                self._list_data[name].append(self._ensure_bytes(value))

            return len(self._list_data[name])

    def lpop(self, name: str, count: Optional[int] = None) -> Optional[str]:
        """Remove and return the first item of the list name"""
        with self._lock:
            if self._check_expiry(name):
                return None
            if name not in self._list_data or not self._list_data[name]:
                return None

            if count is None:
                value = self._list_data[name].pop(0)
            else:
                values = []
                for _ in range(count):
                    values.append(self._list_data[name].pop(0))
                value = values

            # Clean up empty list
            if not self._list_data[name]:
                del self._list_data[name]

            return value

    def rpop(self, name: str) -> Optional[str]:
        """Remove and return the last item of the list name"""
        with self._lock:
            if self._check_expiry(name):
                return None
            if name not in self._list_data or not self._list_data[name]:
                return None

            value = self._list_data[name].pop()

            # Clean up empty list
            if not self._list_data[name]:
                del self._list_data[name]

            return value

    def lrange(self, name: str, start: int, end: int) -> list[str]:
        """Return a slice of the list name between position start and end"""
        with self._lock:
            if self._check_expiry(name):
                return []
            if name not in self._list_data:
                return []

            # Handle negative indices like Redis does
            if end == -1:
                end = len(self._list_data[name])

            return self._list_data[name][start : end + 1]

    def lindex(self, name: str, index: int) -> Optional[str]:
        """Get the element at index in the list name"""
        with self._lock:
            if self._check_expiry(name):
                return None
            try:
                return self._list_data.get(name, [])[index]
            except IndexError:
                return None

    @contextmanager
    def lock(self, key: str, timeout: Optional[int] = None) -> Iterator[None]:
        """Lock a key for a given timeout"""
        if key not in self._lock_data:
            self._lock_data[key] = threading.Lock()
        self._lock_data[key].acquire(timeout)
        yield
        self._lock_data[key].release()

    @contextmanager
    def pipeline(self):
        with self._lock:
            yield InMemoryPipeline(self)


def append_result(func):
    def wrapper(self, *args, **kwargs):
        r = func(self, *args, **kwargs)
        self.results.append(r)
        return r

    return wrapper


class InMemoryPipeline(CacheOperations):
    def __init__(self, cache: InMemoryCache):
        self.cache = cache
        self.results: list[Any] = []

    @append_result
    def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        self.cache.set(key, value, ex)

    @append_result
    def get(self, key: str) -> Optional[str]:
        return self.cache.get(key)

    @append_result
    def keys(self, pattern: str) -> list[str]:
        return self.cache.keys(pattern)

    @append_result
    def delete(self, key: str) -> None:
        self.cache.delete(key)

    @append_result
    def exists(self, key: str) -> bool:
        return self.cache.exists(key)

    @append_result
    def expire(self, key: str, seconds: int) -> bool:
        return self.cache.expire(key, seconds)

    @append_result
    def incr(self, key: str, amount: int = 1) -> int:
        return self.cache.incr(key, amount)

    @append_result
    def decr(self, key: str, amount: int = 1) -> int:
        return self.cache.decr(key, amount)

    @append_result
    def hset(
        self,
        name: str,
        key: Optional[str] = None,
        value: Optional[str] = None,
        mapping: Optional[dict] = None,
    ) -> int:
        return self.cache.hset(name, key, value, mapping)

    @append_result
    def hget(self, name: str, key: str) -> Optional[str]:
        return self.cache.hget(name, key)

    @append_result
    def hgetall(self, name: str) -> dict:
        return self.cache.hgetall(name)

    @append_result
    def hdel(self, name: str, *keys: str) -> int:
        return self.cache.hdel(name, *keys)

    @append_result
    def lpush(self, name: str, *values: str) -> int:
        return self.cache.lpush(name, *values)

    @append_result
    def rpush(self, name: str, *values: str) -> int:
        return self.cache.rpush(name, *values)

    @append_result
    def lpop(self, name: str, count: Optional[int] = None) -> Optional[str]:
        return self.cache.lpop(name, count)

    @append_result
    def rpop(self, name: str) -> Optional[str]:
        return self.cache.rpop(name)

    @append_result
    def lrange(self, name: str, start: int, end: int) -> list[str]:
        return self.cache.lrange(name, start, end)

    @append_result
    def lindex(self, name: str, index: int) -> Optional[str]:
        return self.cache.lindex(name, index)

    def execute(self) -> list[Any]:
        r = self.results
        self.results = []
        return r
