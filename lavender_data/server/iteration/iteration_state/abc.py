from abc import ABC, abstractmethod

from fastapi import HTTPException
from pydantic import BaseModel


from lavender_data.server.reader import (
    GlobalSampleIndex,
)
from lavender_data.server.iteration import ProcessNextSamplesParams


class IterationStateException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


class InProgressIndex(BaseModel):
    index: int
    rank: int
    started_at: float


class Progress(BaseModel):
    total: int
    current: int
    inprogress: list[InProgressIndex]
    completed: int
    filtered: int
    failed: int


class IterationStateOps(ABC):
    @abstractmethod
    def exists(self) -> bool: ...

    @abstractmethod
    def pushback_inprogress(self) -> None: ...

    @abstractmethod
    def complete(self, index: int) -> None: ...

    @abstractmethod
    def filtered(self, index: int) -> None: ...

    @abstractmethod
    def failed(self, index: int) -> None: ...

    @abstractmethod
    def next_item(self, rank: int) -> GlobalSampleIndex: ...

    @abstractmethod
    def get_ranks(self) -> list[int]: ...

    @abstractmethod
    def get_progress(self) -> Progress: ...

    @abstractmethod
    def get_next_samples(self, rank: int) -> tuple[str, ProcessNextSamplesParams]: ...
