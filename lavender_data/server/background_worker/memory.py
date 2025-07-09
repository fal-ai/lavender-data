from multiprocessing import shared_memory as mp_shared_memory
from typing import Union, Optional
import time
import threading
import hashlib
from lavender_data.logging import get_logger

EOF_SIGNATURE = b"EOF"


class SharedMemory:
    def __init__(self):
        self._expiry: dict[str, float] = {}
        self._logger = get_logger(__name__)

        self._start_expiry_thread()

    def _start_expiry_thread(self):
        def check_expiry():
            while True:
                now = time.time()
                expired_keys = [
                    k
                    for k, exp in self._expiry.items()
                    if exp is not None and exp <= now
                ]
                for key in expired_keys:
                    self.delete(key)
                time.sleep(1)

        thread = threading.Thread(target=check_expiry, daemon=True)
        thread.start()

    def _ensure_bytes(self, value: Union[bytes, str]) -> bytes:
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode("utf-8")
        raise ValueError(f"Invalid value type: {type(value)}")

    def _refine_name(self, name: str) -> str:
        return hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]

    def _get_shared_memory(self, name: str) -> mp_shared_memory.SharedMemory:
        return mp_shared_memory.SharedMemory(name=self._refine_name(name))

    def _create_shared_memory(
        self, name: str, size: int
    ) -> mp_shared_memory.SharedMemory:
        self._logger.debug(f"Creating shared memory: {name} {size} bytes")
        return mp_shared_memory.SharedMemory(
            name=self._refine_name(name), create=True, size=size
        )

    def exists(self, name: str) -> bool:
        try:
            self._get_shared_memory(name)
            return True
        except FileNotFoundError:
            return False

    def expire(self, name: str, ex: int):
        self._expiry[name] = time.time() + ex

    def set(self, name: str, value: Union[bytes, str], ex: Optional[int] = None):
        _value = self._ensure_bytes(value)
        _value = (
            len(_value).to_bytes(length=8, byteorder="big", signed=False)
            + _value
            + EOF_SIGNATURE
        )

        try:
            memory = self._create_shared_memory(name, len(_value))
        except FileExistsError:
            memory = self._get_shared_memory(name)

        memory.buf[: len(_value)] = _value

        if ex is not None:
            self._expiry[name] = time.time() + ex
        else:
            self._expiry[name] = None

    def get(self, name: str) -> bytes:
        try:
            memory = self._get_shared_memory(name)
            b = memory.buf.tobytes()
            length = int.from_bytes(b[:8], byteorder="big", signed=False)
            if b[length + 8 : length + 8 + len(EOF_SIGNATURE)] != EOF_SIGNATURE:
                return None
            return b[8 : length + 8]
        except FileNotFoundError:
            return None

    def delete(self, name: str):
        try:
            self._get_shared_memory(name).unlink()
        except FileNotFoundError:
            pass
        try:
            self._expiry.pop(name)
        except KeyError:
            pass

    def clear(self):
        keys = list(self._expiry.keys())
        self._logger.debug(f"Clearing memory: {keys} keys")
        for name in keys:
            self.delete(name)


# singleton
_shared_memory: SharedMemory = None


def setup_shared_memory():
    global _shared_memory
    _shared_memory = SharedMemory()


def get_shared_memory():
    global _shared_memory
    if _shared_memory is None:
        raise RuntimeError("Shared memory not initialized")
    return _shared_memory


def shutdown_shared_memory():
    global _shared_memory
    if _shared_memory is not None:
        _shared_memory.clear()
        _shared_memory = None
