from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.histogram import Histogram


T = TypeVar("T", bound="NumericColumnStatistics")


@_attrs_define
class NumericColumnStatistics:
    """int, float -> value
    string, bytes -> length

        Attributes:
            type_ (Literal['numeric']):
            histogram (Histogram):
            nan_count (int):
            max_ (float):
            min_ (float):
            mean (float):
            median (float):
            std (float):
    """

    type_: Literal["numeric"]
    histogram: "Histogram"
    nan_count: int
    max_: float
    min_: float
    mean: float
    median: float
    std: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        histogram = self.histogram.to_dict()

        nan_count = self.nan_count

        max_ = self.max_

        min_ = self.min_

        mean = self.mean

        median = self.median

        std = self.std

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "histogram": histogram,
                "nan_count": nan_count,
                "max": max_,
                "min": min_,
                "mean": mean,
                "median": median,
                "std": std,
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

        max_ = d.pop("max")

        min_ = d.pop("min")

        mean = d.pop("mean")

        median = d.pop("median")

        std = d.pop("std")

        numeric_column_statistics = cls(
            type_=type_,
            histogram=histogram,
            nan_count=nan_count,
            max_=max_,
            min_=min_,
            mean=mean,
            median=median,
            std=std,
        )

        numeric_column_statistics.additional_properties = d
        return numeric_column_statistics

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
