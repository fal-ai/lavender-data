import pyarrow as pa
import pyarrow.parquet as pq

from .abc import Writer


class ParquetWriter(Writer):
    """Writes a streaming dataset with Parquet format."""

    format: str = "parquet"

    def encode_shard(self, samples: list[dict]) -> bytes:
        """Encode a shard out of the cached samples (single file).

        Returns:
            bytes: File data.
        """
        columns = samples[0].keys()
        data = {k: [d[k] for d in samples] for k in columns}
        table = pa.Table.from_pydict(data)
        data_sink = pa.BufferOutputStream()
        pq.write_table(table, data_sink)
        return data_sink.getvalue().to_pybytes()
