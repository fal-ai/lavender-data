from typing import Literal, TypedDict, Union

import numpy as np

from lavender_data.shard.statistics import (
    CategoricalShardStatistics,
    NumericShardStatistics,
    get_outlier_aware_hist,
)
from lavender_data.server.db.models import DatasetColumn, Dataset
from lavender_data.logging import get_logger


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


def _merge_histograms(histograms: list[Histogram]) -> tuple[Histogram, list[float]]:
    _restored_values = []

    for histogram in histograms:
        hist = histogram["hist"]
        bin_edges = histogram["bin_edges"]

        for i in range(len(hist)):
            _min = bin_edges[i]
            _max = bin_edges[i + 1]
            _count = int(hist[i])
            if _count == 0:
                continue
            elif _count == 1:
                if i == len(hist) - 1:
                    _restored_values.append(_max)
                else:
                    _restored_values.append(_min)
            else:
                _restored_values.append(_min)
                _gap = (_max - _min) / (_count - 1)
                _restored_values.extend([_min + j * _gap for j in range(1, _count - 1)])
                _restored_values.append(_max)

    return get_outlier_aware_hist(_restored_values), _restored_values


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
    _all_histograms = []
    _nan_count = 0
    _max = None
    _min = None
    _sum = 0
    _sum_squared = 0
    _count = 0
    for shard_statistic in shard_statistics:
        _all_histograms.append(shard_statistic["histogram"])
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
    _histogram, _restored_values = _merge_histograms(_all_histograms)
    _median = np.median(_restored_values).item()

    return NumericColumnStatistics(
        type="numeric",
        histogram=_histogram,
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


def get_dataset_statistics(dataset: Dataset) -> dict[str, ColumnStatistics]:
    logger = get_logger(__name__)
    statistics = {}
    for column in dataset.columns:
        try:
            statistics[column.name] = get_column_statistics(column)
        except Exception as e:
            logger.warning(f"Failed to get statistics for column {column.name}: {e}")
    return statistics
