import os
import csv
import sys
import ast
from typing import Any

from .abc import UntypedReader

__all__ = ["CsvReader"]

csv.field_size_limit(sys.maxsize)


class CsvReader(UntypedReader):
    format = "csv"
    typed_columns = False

    def resolve_type(self, value: Any, typestr: str) -> type:
        if typestr in ["int32", "int64"]:
            return int(value)
        elif typestr in ["float", "double"]:
            return float(value)
        elif typestr in ["string"]:
            return str(value)
        elif typestr in ["boolean"]:
            return value.lower() in ["true", "t", "yes", "y", "1"]
        elif typestr in ["list", "map", "binary"]:
            return ast.literal_eval(value)
        return value

    def read_columns(self) -> dict[str, str]:
        with open(self.filepath, "r") as f:
            reader = csv.DictReader(f)
            return {name: "string" for name in reader.fieldnames}

    def read_samples(self) -> list[dict[str, Any]]:
        samples = []
        with open(self.filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                samples.append(
                    {
                        key: self.resolve_type(value, self.columns[key])
                        for key, value in row.items()
                        if key in self.columns
                    }
                )
        return samples
