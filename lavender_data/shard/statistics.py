import math
import numpy as np
import sys
from typing import Any, Literal, Optional, Union

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from lavender_data.logging import get_logger


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
    median: float
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
    # unhashable types are not categorical
    if not _is_numeric_column(values) and not _is_text_column(values):
        return False

    unique_values = set(values)

    if _is_numeric_column(values):
        return len(set(values)) <= 10

    return len(unique_values) <= max(min(len(values) * 0.1, 99), 2)


def _get_categorical_statistics(values: list[Any]) -> CategoricalShardStatistics:
    nan_count = 0
    frequencies = {}
    for value in values:
        if value is None or value == "" or value == b"":
            nan_count += 1
            continue
        frequencies[str(value)] = frequencies.get(str(value), 0) + 1

    return CategoricalShardStatistics(
        type="categorical",
        frequencies=frequencies,
        n_unique=len(frequencies.keys()),
        nan_count=nan_count,
    )


def get_outlier_aware_hist(values: list[Union[int, float]]) -> Histogram:
    np_values = np.array(values)
    median = np.median(values)
    diff = np.abs(values - median)
    mad = np.median(diff)
    const = 3.5 * mad / 0.6745
    min_value = np_values.min().item()
    max_value = np_values.max().item()
    lower_bound, upper_bound = (
        max(median - const, min_value),
        min(median + const, max_value),
    )

    n_lower_outliers = (np_values < lower_bound).sum().item()
    n_upper_outliers = (np_values > upper_bound).sum().item()

    num_unique_values = len(set([int(v * 100) for v in values if v != np.nan]))
    max_bins = min(num_unique_values, 10)
    if n_lower_outliers > 0:
        max_bins -= 1
    if n_upper_outliers > 0:
        max_bins -= 1
    max_bins = max(max_bins, 1)

    if max_bins == 1:
        bins = [min_value, max_value]
    else:
        bins = max_bins

    _hist, _bin_edges = np.histogram(
        values, range=(lower_bound, upper_bound), bins=bins
    )
    hist: list[float] = _hist.tolist()
    bin_edges: list[float] = _bin_edges.tolist()

    if n_lower_outliers > 0:
        hist.insert(0, n_lower_outliers)
        bin_edges.insert(0, min_value)
    if n_upper_outliers > 0:
        hist.append(n_upper_outliers)
        bin_edges.append(max_value)

    return Histogram(hist=hist, bin_edges=bin_edges)


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

    elif isinstance(values[0], (list, tuple)):

        def _to_numeric(value: Any):
            if value is None:
                return None
            return len(value)

    elif isinstance(values[0], dict):

        def _to_numeric(value: Any):
            if value is None:
                return None
            return len(value.keys())

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
        histogram=get_outlier_aware_hist(numeric_values),
        nan_count=_nan_count,
        count=len(numeric_values),
        max=_max,
        min=_min,
        sum=_sum,
        median=np.median(numeric_values).item(),
        sum_squared=_sum_squared,
    )


def get_shard_column_statistics(
    values: list[Any],
    statistics_type: Optional[Literal["numeric", "categorical"]] = None,
) -> ShardColumnStatistics:
    if statistics_type == "categorical":
        return _get_categorical_statistics(values)
    elif statistics_type == "numeric":
        return _get_numeric_statistics(values)

    if _is_categorical_column(values):
        return _get_categorical_statistics(values)

    return _get_numeric_statistics(values)


def get_shard_statistics(
    samples: list[dict[str, Any]],
    columns: dict[str, str],
    statistics_types: Optional[dict[str, Literal["numeric", "categorical"]]] = None,
) -> ShardStatistics:
    logger = get_logger(__name__)
    samples_by_column = {
        column_name: [sample[column_name] for sample in samples]
        for column_name in columns.keys()
    }

    column_statistics = {}
    for column_name, values in samples_by_column.items():
        statistics_type = (
            statistics_types.get(column_name) if statistics_types else None
        )
        try:
            column_statistics[column_name] = get_shard_column_statistics(
                values, statistics_type=statistics_type
            )
        except Exception as e:
            logger.warning(f"Error getting statistics for column {column_name}: {e}")
            continue

    return column_statistics
