from typing import Literal, TypedDict, Union

import numpy as np

from lavender_data.shard.statistics import (
    CategoricalShardStatistics,
    NumericShardStatistics,
)
from lavender_data.server.db.models import DatasetColumn


class Histogram(TypedDict):
    hist: list[float]
    bin_edges: list[float]


class NumericColumnStatistics(TypedDict):
    """
    int, float -> value
    string, bytes -> length
    """

    type: Literal["numeric"]
    histogram: Histogram
    nan_count: int
    max: float
    min: float
    mean: float
    median: float
    std: float


class CategoricalColumnStatistics(TypedDict):
    type: Literal["categorical"]
    frequencies: dict[str, int]
    n_unique: int
    nan_count: int


ColumnStatistics = Union[NumericColumnStatistics, CategoricalColumnStatistics]


def _merge_histograms(
    hist: list[float], bin_edges: list[float]
) -> tuple[list[float], list[float]]:
    _map = {}
    for v, bin_edge in zip(hist, bin_edges):
        _map[bin_edge] = _map.get(bin_edge, 0) + v

    _restored_values = []
    _bin_edges = sorted(_map.keys())
    for _value in _bin_edges:
        h = _map[_value]
        _restored_values.extend([_value] * int(h))

    num_unique_values = len(
        set([int(v * 100) for v in _restored_values if v is not None])
    )
    _hist, _bin_edges = np.histogram(_restored_values, bins=min(num_unique_values, 10))
    return _hist.tolist(), _bin_edges.tolist()


def aggregate_categorical_statistics(
    shard_statistics: list[CategoricalShardStatistics],
) -> CategoricalColumnStatistics:
    """
    Aggregate categorical statistics from multiple shards.
    """
    nan_count = 0
    frequencies = {}
    for shard_statistic in shard_statistics:
        for key, value in shard_statistic["frequencies"].items():
            frequencies[key] = frequencies.get(key, 0) + value
        nan_count += shard_statistic["nan_count"]

    return CategoricalColumnStatistics(
        type="categorical",
        frequencies=frequencies,
        n_unique=len(frequencies.keys()),
        nan_count=nan_count,
    )


def aggregate_numeric_statistics(
    shard_statistics: list[NumericShardStatistics],
) -> NumericColumnStatistics:
    """
    Aggregate numeric statistics from multiple shards.
    """
    _all_hist = []
    _all_bin_edges = []
    _nan_count = 0
    _max = None
    _min = None
    _sum = 0
    _sum_squared = 0
    _count = 0
    for shard_statistic in shard_statistics:
        _all_hist.extend(shard_statistic["histogram"]["hist"])
        _all_bin_edges.extend(shard_statistic["histogram"]["bin_edges"])
        _nan_count += shard_statistic["nan_count"]
        if _max is None or shard_statistic["max"] > _max:
            _max = shard_statistic["max"]
        if _min is None or shard_statistic["min"] < _min:
            _min = shard_statistic["min"]
        _sum += shard_statistic["sum"]
        _sum_squared += shard_statistic["sum_squared"]
        _count += shard_statistic["count"]

    _mean = _sum / _count
    # E[X^2] - (E[X])^2
    _std = np.sqrt(_sum_squared / _count - _mean**2).item()

    # estimate median from histogram
    _median = 0
    _seen = 0
    for i in range(len(_all_bin_edges) - 1):
        _seen += _all_hist[i]
        if _seen <= _count // 2 <= _seen + _all_hist[i + 1]:
            _median = (_all_bin_edges[i] + _all_bin_edges[i + 1]) / 2
            break

    _hist, _bin_edges = _merge_histograms(_all_hist, _all_bin_edges)

    return NumericColumnStatistics(
        type="numeric",
        histogram=Histogram(hist=_hist, bin_edges=_bin_edges),
        nan_count=_nan_count,
        max=_max,
        min=_min,
        mean=_mean,
        median=_median,
        std=_std,
    )


def get_column_statistics(column: DatasetColumn) -> ColumnStatistics:
    shard_statistics = [
        shard.statistics[column.name]
        for shard in column.shardset.shards
        if shard.statistics is not None
    ]
    if len(shard_statistics) == 0:
        raise ValueError(f"No shard statistics found for column {column.name}")

    if shard_statistics[0]["type"] == "categorical":
        return aggregate_categorical_statistics(shard_statistics)
    elif shard_statistics[0]["type"] == "numeric":
        return aggregate_numeric_statistics(shard_statistics)
    else:
        raise ValueError(f"Unknown column statistics: {column.name} {shard_statistics}")
