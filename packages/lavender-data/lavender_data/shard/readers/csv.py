import os
import csv
import ast
from typing import Any

from .abc import Reader

__all__ = ["CsvReader"]


class CsvReader(Reader):
    format = "csv"

    def resolve_type(self, value: Any, typestr: str) -> type:
        if typestr == "int":
            return int(value)
        elif typestr == "float":
            return float(value)
        elif typestr == "str":
            return str(value)
        elif (
            typestr == "list"
            or typestr == "tuple"
            or typestr == "set"
            or typestr == "dict"
            or typestr == "bytes"
            or typestr == "ndarray"  # stored in bytes, use serializer
        ):
            return ast.literal_eval(value)
        return value

    def read_samples(self) -> list[dict[str, Any]]:
        samples = []
        with open(self.filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                samples.append(
                    {
                        key: self.resolve_type(value, self.columns[key])
                        for key, value in row.items()
                    }
                )
        return samples
