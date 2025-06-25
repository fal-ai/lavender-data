from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.histogram import Histogram


T = TypeVar("T", bound="NumericShardStatistics")


@_attrs_define
class NumericShardStatistics:
    """
    Attributes:
        type_ (Literal['numeric']):
        histogram (Histogram):
        nan_count (int):
        count (int):
        max_ (float):
        min_ (float):
        sum_ (float):
        median (float):
        sum_squared (float):
    """

    type_: Literal["numeric"]
    histogram: "Histogram"
    nan_count: int
    count: int
    max_: float
    min_: float
    sum_: float
    median: float
    sum_squared: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        histogram = self.histogram.to_dict()

        nan_count = self.nan_count

        count = self.count

        max_ = self.max_

        min_ = self.min_

        sum_ = self.sum_

        median = self.median

        sum_squared = self.sum_squared

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "histogram": histogram,
                "nan_count": nan_count,
                "count": count,
                "max": max_,
                "min": min_,
                "sum": sum_,
                "median": median,
                "sum_squared": sum_squared,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.histogram import Histogram

        d = dict(src_dict)
        type_ = cast(Literal["numeric"], d.pop("type"))
        if type_ != "numeric":
            raise ValueError(f"type must match const 'numeric', got '{type_}'")

        histogram = Histogram.from_dict(d.pop("histogram"))

        nan_count = d.pop("nan_count")

        count = d.pop("count")

        max_ = d.pop("max")

        min_ = d.pop("min")

        sum_ = d.pop("sum")

        median = d.pop("median")

        sum_squared = d.pop("sum_squared")

        numeric_shard_statistics = cls(
            type_=type_,
            histogram=histogram,
            nan_count=nan_count,
            count=count,
            max_=max_,
            min_=min_,
            sum_=sum_,
            median=median,
            sum_squared=sum_squared,
        )

        numeric_shard_statistics.additional_properties = d
        return numeric_shard_statistics

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
