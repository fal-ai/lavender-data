import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Optional
from typing_extensions import Self
import tempfile

from lavender_data.storage import upload_file
from lavender_data.client.api import create_shard, get_dataset

__all__ = ["Writer", "type_to_str"]

logger = logging.getLogger(__name__)


def type_to_str(value: Any) -> str:
    return type(value).__name__


def get_columns_from_samples(samples: list[dict]) -> dict[str, str]:
    return {key: type_to_str(value) for key, value in samples[0].items()}


class Writer(ABC):
    format: str = ""  # Name of the format (like "parquet", etc).

    @classmethod
    def get(
        cls,
        format: str,
        dataset_id: str,
        shardset_id: str,
        persist_files: bool = False,
        **kwargs,
    ) -> Self:
        for subcls in cls.__subclasses__():
            if format == subcls.format:
                try:
                    instance = subcls(dataset_id, shardset_id, persist_files, **kwargs)
                    return instance
                except ImportError as e:
                    raise ImportError(
                        f"Please install required dependencies for {subcls.__name__}"
                    ) from e
        raise ValueError(f"Invalid format: {format}")

    def __init__(self, dataset_id: str, shardset_id: str, persist_files: bool = False):
        self.dataset = get_dataset(dataset_id)
        try:
            self.shardset = next(
                s for s in self.dataset.shardsets if s.id == shardset_id
            )
        except StopIteration:
            raise ValueError(
                f"Shardset {shardset_id} not found in dataset {dataset_id}"
            )
        self.persist_files = persist_files

    def encode_sample(self, sample: dict) -> dict:
        return sample

    @abstractmethod
    def encode_shard(self, samples: list[dict]) -> bytes:
        """Encode a shard to bytes.

        Returns:
            bytes: Shard encoded as bytes.
        """
        raise NotImplementedError

    def write(
        self,
        shard_index: int,
        samples: list[dict],
        location: Optional[str] = None,
        filename: Optional[str] = None,
        overwrite: bool = False,
    ):
        if len(samples) == 0:
            raise ValueError("No samples to write")

        encoded_samples = [self.encode_sample(sample) for sample in samples]
        raw_data = self.encode_shard(encoded_samples)

        if filename is None:
            f = tempfile.NamedTemporaryFile(delete=False)
            filename = f.name
        else:
            f = open(filename, "wb")

        f.write(raw_data)
        f.close()

        _location = location or os.path.join(
            self.shardset.location, f"shard.{shard_index:05}.{self.format}"
        )

        upload_file(filename, _location, delete_after_upload=True)
        shard = create_shard(
            dataset_id=self.dataset.id,
            shardset_id=self.shardset.id,
            index=shard_index,
            location=_location,
            filesize=len(raw_data),
            samples=len(samples),
            format=self.format,
            overwrite=overwrite,
        )

        if not self.persist_files:
            os.remove(filename)

        return shard
