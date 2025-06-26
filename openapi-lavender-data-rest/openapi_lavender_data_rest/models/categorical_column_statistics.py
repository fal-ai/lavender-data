from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.categorical_column_statistics_frequencies import CategoricalColumnStatisticsFrequencies


T = TypeVar("T", bound="CategoricalColumnStatistics")


@_attrs_define
class CategoricalColumnStatistics:
    """
    Attributes:
        type_ (Literal['categorical']):
        frequencies (CategoricalColumnStatisticsFrequencies):
        n_unique (int):
        nan_count (int):
    """

    type_: Literal["categorical"]
    frequencies: "CategoricalColumnStatisticsFrequencies"
    n_unique: int
    nan_count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        frequencies = self.frequencies.to_dict()

        n_unique = self.n_unique

        nan_count = self.nan_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "frequencies": frequencies,
                "n_unique": n_unique,
                "nan_count": nan_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.categorical_column_statistics_frequencies import CategoricalColumnStatisticsFrequencies

        d = dict(src_dict)
        type_ = cast(Literal["categorical"], d.pop("type"))
        if type_ != "categorical":
            raise ValueError(f"type must match const 'categorical', got '{type_}'")

        frequencies = CategoricalColumnStatisticsFrequencies.from_dict(d.pop("frequencies"))

        n_unique = d.pop("n_unique")

        nan_count = d.pop("nan_count")

        categorical_column_statistics = cls(
            type_=type_,
            frequencies=frequencies,
            n_unique=n_unique,
            nan_count=nan_count,
        )

        categorical_column_statistics.additional_properties = d
        return categorical_column_statistics

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
