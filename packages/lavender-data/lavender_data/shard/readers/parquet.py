""":class:`ParquetReader` reads samples from `.parquet` files that were written by :class:`ParquetWriter`."""

import os
from typing import Any

import pyarrow.parquet as pq

from .abc import Reader

__all__ = ["ParquetReader"]


class ParquetReader(Reader):
    format = "parquet"

    def read_samples(self) -> list[dict[str, Any]]:
        return pq.read_table(
            self.filepath, columns=list(self.columns.keys())
        ).to_pylist()
