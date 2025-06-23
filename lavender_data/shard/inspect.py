import os
import tempfile
from typing import Literal, Optional

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


def inspect_shard(
    shard_location: str,
    statistics_types: Optional[dict[str, Literal["numeric", "categorical"]]] = None,
    known_columns: Optional[dict[str, str]] = None,
) -> OrphanShardInfo:
    shard_format = os.path.splitext(shard_location)[1].lstrip(".")

    with tempfile.NamedTemporaryFile() as f:
        reader = Reader.get(
            location=shard_location,
            format=shard_format,
            filepath=f.name,
            columns=known_columns,
        )
        filesize = os.path.getsize(f.name)
        columns = reader.columns
        samples = [s for s in reader]
        statistics = get_shard_statistics(
            samples=samples,
            columns=columns,
            statistics_types=statistics_types,
        )

    return OrphanShardInfo(
        samples=len(samples),
        location=shard_location,
        format=shard_format,
        filesize=filesize,
        columns=columns,
        statistics=statistics,
    )
