import os
from abc import ABC, abstractmethod
from typing import Any, Iterator, Optional, Union
from typing_extensions import Self

from lavender_data.storage import download_file
from lavender_data.logging import get_logger

from .exceptions import (
    ReaderColumnsRequired,
    ReaderColumnsInvalid,
    ReaderFormatInvalid,
    ReaderDirnameOrFilepathRequired,
)

__all__ = ["Reader"]

logger = get_logger(__name__)


class Reader(ABC):
    format: str = ""

    @classmethod
    def get(
        cls,
        format: str,
        location: str,
        *,
        columns: Optional[dict[str, str]] = None,
        dirname: Optional[str] = None,
        filepath: Optional[str] = None,
        uid_column_name: Optional[str] = None,
        uid_column_type: Optional[str] = None,
    ) -> Union[Self, "UntypedReader", "TypedReader"]:
        for subcls in cls._reader_classes():
            if format == subcls.format:
                try:
                    instance = subcls(
                        location=location,
                        columns=columns,
                        dirname=dirname,
                        filepath=filepath,
                        uid_column_name=uid_column_name,
                        uid_column_type=uid_column_type,
                    )
                    if isinstance(instance, UntypedReader) and columns is None:
                        logger.warning(
                            f'Shard is in "{format}" format, which is not a typed format. '
                            'All columns will be read as "str".'
                        )

                    # TODO async?
                    instance.prepare()

                    if columns is None:
                        instance.columns = instance.read_columns()

                    return instance
                except ImportError as e:
                    raise ImportError(
                        f"Please install required dependencies for {subcls.__name__}"
                    ) from e
        raise ReaderFormatInvalid(f"Invalid format: {format}")

    @classmethod
    def _reader_classes(cls):
        classes = []
        for subcls in cls.__subclasses__():
            if subcls.format:
                classes.append(subcls)
            else:
                classes.extend(subcls._reader_classes())
        return classes

    def __init__(
        self,
        location: str,
        columns: dict[str, str],
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
            raise ReaderDirnameOrFilepathRequired()

        self.location = location
        self.columns = columns
        self.uid_column_name = uid_column_name
        self.uid_column_type = uid_column_type

        if self.columns is not None and self.uid_column_name not in self.columns:
            self.columns[self.uid_column_name] = self.uid_column_type

        self.loaded: bool = False
        self.uids: list[Union[str, int]] = []
        self.cache: dict[Union[str, int], dict[str, Any]] = {}

    def with_columns(self, columns: list[str]):
        new_columns = {}
        for column in columns:
            if column not in self.columns:
                raise ReaderColumnsInvalid(f"Column {column} not found")
            new_columns[column] = self.columns[column]
        self.columns = new_columns

    def prepare(self):
        try:
            download_file(self.location, self.filepath)
        except Exception as e:
            # TODO
            raise e

    def __len__(self) -> int:
        if not self.loaded:
            self._load()
        return len(self.uids)

    def get_item(self, key: int) -> dict[str, Any]:
        return self.get_item_by_index(key)

    @abstractmethod
    def read_columns(self) -> dict[str, str]:
        raise NotImplementedError

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


class TypedReader(Reader):
    pass


class UntypedReader(Reader):
    @abstractmethod
    def resolve_type(self, value: Any, typestr: str) -> type:
        raise NotImplementedError
