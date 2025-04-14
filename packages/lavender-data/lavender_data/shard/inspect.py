import os
import tempfile

from typing import NamedTuple

from .readers import Reader


class OrphanShardInfo(NamedTuple):
    samples: int
    location: str
    format: str
    filesize: int
    columns: dict[str, str]


def inspect_shard(shard_location: str) -> OrphanShardInfo:
    shard_format = os.path.splitext(shard_location)[1].lstrip(".")

    with tempfile.NamedTemporaryFile() as f:
        reader = Reader.get(
            location=shard_location,
            format=shard_format,
            filepath=f.name,
        )
        filesize = os.path.getsize(f.name)
        samples = len(reader)
        columns = reader.columns

    return OrphanShardInfo(
        samples=samples,
        location=shard_location,
        format=shard_format,
        filesize=filesize,
        columns=columns,
    )
