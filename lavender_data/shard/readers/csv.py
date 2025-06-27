import numpy as np
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
        if typestr in ["int", "int32", "int64"]:
            if value == "":
                return np.nan
            return int(value)
        elif typestr in ["float", "double"]:
            if value == "":
                return np.nan
            return float(value)
        elif typestr in ["string", "text", "str"]:
            return str(value)
        elif typestr in ["bool", "boolean"]:
            return value.lower() in ["true", "t", "yes", "y", "1"]
        elif typestr in ["list"]:
            if value == "":
                return []
            return ast.literal_eval(value)
        elif typestr in ["map"]:
            if value == "":
                return {}
            return ast.literal_eval(value)
        elif typestr in ["binary"]:
            if value == "":
                return b""
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
