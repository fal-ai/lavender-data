import os
from abc import ABC, abstractmethod
from typing import Any, Iterator, Optional, Union
from typing_extensions import Self

from lavender_data.storage import download_file

__all__ = ["Reader"]


class Reader(ABC):
    format: str = ""

    @classmethod
    def get(
        cls,
        format: str,
        location: str,
        samples: int,
        columns: Optional[dict[str, str]] = None,
        *,
        dirname: Optional[str] = None,
        filepath: Optional[str] = None,
        uid_column_name: Optional[str] = None,
        uid_column_type: Optional[str] = None,
    ) -> Self:
        for subcls in cls.__subclasses__():
            if format == subcls.format:
                try:
                    instance = subcls(
                        location=location,
                        samples=samples,
                        columns=columns,
                        dirname=dirname,
                        filepath=filepath,
                        uid_column_name=uid_column_name,
                        uid_column_type=uid_column_type,
                    )
                    # TODO async?
                    instance.prepare()
                    return instance
                except ImportError as e:
                    raise ImportError(
                        f"Please install required dependencies for {subcls.__name__}"
                    ) from e
        raise ValueError(f"Invalid format: {format}")

    def __init__(
        self,
        location: str,
        samples: int,
        columns: Optional[dict[str, str]] = None,
        *,
        dirname: Optional[str] = None,
        filepath: Optional[str] = None,
        uid_column_name: Optional[str] = None,
        uid_column_type: Optional[str] = None,
        **kwargs,
    ) -> None:
        if dirname:
            self.filepath = os.path.join(dirname, os.path.basename(location))
        elif filepath:
            self.filepath = filepath
        else:
            raise ValueError("One of dirname or filepath must be specified")

        self.location = location
        self.samples = samples
        self.columns = columns
        self.uid_column_name = uid_column_name
        self.uid_column_type = uid_column_type

        if self.uid_column_name not in self.columns:
            self.columns[self.uid_column_name] = self.uid_column_type

        self.loaded: bool = False
        self.uids: list[Union[str, int]] = []
        self.cache: dict[Union[str, int], dict[str, Any]] = {}

    def with_columns(self, columns: list[str]):
        new_columns = {}
        for column in columns:
            if column not in self.columns:
                raise ValueError(f"Column {column} not found")
            new_columns[column] = self.columns[column]
        self.columns = new_columns

    def prepare(self):
        try:
            download_file(self.location, self.filepath)
        except Exception as e:
            # TODO
            raise e

    @property
    def size(self):
        return self.samples

    def __len__(self) -> int:
        return self.samples

    def get_item(self, key: int) -> dict[str, Any]:
        return self.get_item_by_index(key)

    @abstractmethod
    def read_samples(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def _load(self) -> None:
        if self.loaded:
            return
        samples = self.read_samples()
        for i, sample in enumerate(samples):
            if self.uid_column_name is not None:
                uid = sample[self.uid_column_name]
            else:
                uid = i
            self.uids.append(uid)
            self.cache[uid] = sample
        self.loaded = True

    def get_item_by_index(self, idx: int) -> dict[str, Any]:
        if not self.loaded:
            self._load()
        return self.get_item_by_uid(self.uids[idx])

    def get_item_by_uid(self, uid: str) -> dict[str, Any]:
        if not self.loaded:
            self._load()
        return self.cache[uid]

    def __iter__(self) -> Iterator[dict[str, Any]]:
        for i in range(len(self)):
            yield self[i]
