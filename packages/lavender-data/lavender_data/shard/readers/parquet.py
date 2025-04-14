""":class:`ParquetReader` reads samples from `.parquet` files that were written by :class:`ParquetWriter`."""

from typing import Any

import pyarrow.parquet as pq

from .abc import TypedReader

__all__ = ["ParquetReader"]


class ParquetReader(TypedReader):
    format = "parquet"

    def read_columns(self) -> dict[str, str]:
        schema = pq.read_schema(
            self.filepath,
        )
        return {
            name: str(pa_dtype) for name, pa_dtype in zip(schema.names, schema.types)
        }

    def read_samples(self) -> list[dict[str, Any]]:
        return pq.read_table(
            self.filepath, columns=list(self.columns.keys())
        ).to_pylist()
