from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.categorical_shard_statistics_frequencies import CategoricalShardStatisticsFrequencies


T = TypeVar("T", bound="CategoricalShardStatistics")


@_attrs_define
class CategoricalShardStatistics:
    """
    Attributes:
        type_ (Literal['categorical']):
        nan_count (int):
        n_unique (int):
        frequencies (CategoricalShardStatisticsFrequencies):
    """

    type_: Literal["categorical"]
    nan_count: int
    n_unique: int
    frequencies: "CategoricalShardStatisticsFrequencies"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        nan_count = self.nan_count

        n_unique = self.n_unique

        frequencies = self.frequencies.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "nan_count": nan_count,
                "n_unique": n_unique,
                "frequencies": frequencies,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.categorical_shard_statistics_frequencies import CategoricalShardStatisticsFrequencies

        d = dict(src_dict)
        type_ = cast(Literal["categorical"], d.pop("type"))
        if type_ != "categorical":
            raise ValueError(f"type must match const 'categorical', got '{type_}'")

        nan_count = d.pop("nan_count")

        n_unique = d.pop("n_unique")

        frequencies = CategoricalShardStatisticsFrequencies.from_dict(d.pop("frequencies"))

        categorical_shard_statistics = cls(
            type_=type_,
            nan_count=nan_count,
            n_unique=n_unique,
            frequencies=frequencies,
        )

        categorical_shard_statistics.additional_properties = d
        return categorical_shard_statistics

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
