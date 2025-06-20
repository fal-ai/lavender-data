import os
import tempfile

from pydantic import BaseModel

from .readers import Reader
from .statistics import get_shard_statistics, ShardStatistics


class OrphanShardInfo(BaseModel):
    samples: int
    location: str
    format: str
    filesize: int
    columns: dict[str, str]
    statistics: ShardStatistics


def inspect_shard(shard_location: str) -> OrphanShardInfo:
    shard_format = os.path.splitext(shard_location)[1].lstrip(".")

    with tempfile.NamedTemporaryFile() as f:
        reader = Reader.get(
            location=shard_location,
            format=shard_format,
            filepath=f.name,
        )
        filesize = os.path.getsize(f.name)
        columns = reader.columns
        samples = [s for s in reader]
        statistics = get_shard_statistics(
            samples=samples,
            columns=columns,
        )

    return OrphanShardInfo(
        samples=len(samples),
        location=shard_location,
        format=shard_format,
        filesize=filesize,
        columns=columns,
        statistics=statistics,
    )
