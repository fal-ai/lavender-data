import io
import csv
from typing import Any

from .abc import Writer


class CsvWriter(Writer):
    """Writes a streaming dataset with CSV format."""

    format: str = "csv"

    def encode_shard(self, samples: list[dict]) -> bytes:
        """Encode a shard out of the cached samples (single file).

        Returns:
            bytes: File data.
        """
        memfile = io.StringIO()
        writer = csv.DictWriter(memfile, fieldnames=samples[0].keys())
        writer.writeheader()
        writer.writerows(samples)
        return memfile.getvalue().encode("utf-8")
