from multiprocessing import shared_memory
from typing import Union, Optional
import time
import threading
import hashlib
import json
from pydantic import BaseModel
from lavender_data.logging import get_logger


class TaskStatus(BaseModel):
    status: str
    current: int
    total: int


class Memory:
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

    def _get_shared_memory(self, name: str) -> shared_memory.SharedMemory:
        return shared_memory.SharedMemory(name=self._refine_name(name))

    def _create_shared_memory(self, name: str, size: int) -> shared_memory.SharedMemory:
        return shared_memory.SharedMemory(
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
        _value = len(_value).to_bytes(length=8, byteorder="big", signed=False) + _value

        if self.exists(name):
            self._get_shared_memory(name).unlink()

        memory = self._create_shared_memory(name, len(_value))
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
            return b[8 : length + 8]
        except FileNotFoundError:
            return None

    def delete(self, name: str):
        try:
            self._get_shared_memory(name).unlink()
        except FileNotFoundError:
            pass

    def clear(self):
        self._logger.debug(f"Clearing memory: {len(self._expiry)} keys")
        for name in self._expiry.keys():
            self.delete(name)

    def get_task_status(self, task_uid: str) -> Optional[TaskStatus]:
        status = self.get(f"task-{task_uid}")
        if status is None:
            return None

        try:
            status = json.loads(status)
        except Exception:
            return None

        return TaskStatus.model_validate(status)

    def set_task_status(
        self,
        task_uid: str,
        status: Optional[str] = None,
        current: Optional[int] = None,
        total: Optional[int] = None,
        ex: Optional[int] = None,
    ):
        _status = self.get_task_status(task_uid)
        if _status is None:
            _status = TaskStatus(status="", current=0, total=0)

        self.set(
            f"task-{task_uid}",
            json.dumps(
                {
                    "status": status if status is not None else _status.status,
                    "current": current if current is not None else _status.current,
                    "total": total if total is not None else _status.total,
                }
            ),
            ex=ex,
        )

    def delete_task_status(self, task_uid: str):
        self.delete(f"task-{task_uid}")
