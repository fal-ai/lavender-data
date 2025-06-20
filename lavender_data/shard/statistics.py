import math
import numpy as np
from typing import Any, Literal, TypedDict, Union


class Histogram(TypedDict):
    hist: list[float]
    bin_edges: list[float]


class NumericShardStatistics(TypedDict):
    type: Literal["numeric"]
    histogram: Histogram
    nan_count: int
    count: int
    max: float
    min: float
    sum: float
    sum_squared: float


class CategoricalShardStatistics(TypedDict):
    type: Literal["categorical"]
    nan_count: int
    n_unique: int
    frequencies: dict[str, int]


ShardColumnStatistics = Union[NumericShardStatistics, CategoricalShardStatistics]

ShardStatistics = dict[str, ShardColumnStatistics]


def _is_numeric_column(values: list[Any]) -> bool:
    if isinstance(values[0], (int, float)):
        return True
    return False


def _is_text_column(values: list[Any]) -> bool:
    if isinstance(values[0], (str, bytes)):
        return True
    return False


def _is_categorical_column(values: list[Any]) -> bool:
    if not _is_text_column(values):
        return False

    unique_values = set(values)
    return len(unique_values) <= max(len(values) * 0.1, 1)


def _get_categorical_statistics(values: list[Any]) -> CategoricalShardStatistics:
    nan_count = 0
    frequencies = {}
    for value in values:
        if value is None or value == "" or value == b"":
            nan_count += 1
            continue
        frequencies[value] = frequencies.get(value, 0) + 1

    return CategoricalShardStatistics(
        type="categorical",
        frequencies=frequencies,
        n_unique=len(frequencies.keys()),
        nan_count=nan_count,
    )


def _get_histogram(values: list[Union[int, float]]) -> Histogram:
    num_unique_values = len(set([int(v * 100) for v in values if v is not None]))
    hist, bin_edges = np.histogram(values, bins=min(num_unique_values, 10))
    return Histogram(hist=hist.tolist(), bin_edges=bin_edges.tolist())


def _get_numeric_statistics(values: list[Any]) -> NumericShardStatistics:
    _nan_count = 0
    _max = None
    _min = None
    _sum = 0
    _sum_squared = 0

    if _is_numeric_column(values):

        def _to_numeric(value: Any):
            if value is None or math.isnan(value):
                return None
            return value

    elif _is_text_column(values):

        def _to_numeric(value: Any):
            if value is None or value == "":
                return None
            return len(value)

    else:
        raise ValueError(f"Invalid column type: {type(values[0])}")

    numeric_values = []
    for value in values:
        _value = _to_numeric(value)

        if _value is None:
            _nan_count += 1
            continue

        numeric_values.append(_value)
        _sum += _value
        _sum_squared += _value**2
        if _max is None or _value > _max:
            _max = _value
        if _min is None or _value < _min:
            _min = _value

    return NumericShardStatistics(
        type="numeric",
        histogram=_get_histogram(numeric_values),
        nan_count=_nan_count,
        count=len(numeric_values),
        max=_max,
        min=_min,
        sum=_sum,
        sum_squared=_sum_squared,
    )


def get_shard_column_statistics(
    values: list[Any],
) -> ShardColumnStatistics:
    if _is_categorical_column(values):
        return _get_categorical_statistics(values)

    return _get_numeric_statistics(values)


def get_shard_statistics(
    samples: list[dict[str, Any]],
    columns: dict[str, str],
) -> ShardStatistics:
    samples_by_column = {
        column_name: [sample[column_name] for sample in samples]
        for column_name in columns.keys()
    }

    column_statistics = {}
    for column_name, values in samples_by_column.items():
        column_statistics[column_name] = get_shard_column_statistics(values)

    return column_statistics
