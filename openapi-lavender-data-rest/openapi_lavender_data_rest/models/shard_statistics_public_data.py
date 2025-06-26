from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.categorical_shard_statistics import CategoricalShardStatistics
    from ..models.numeric_shard_statistics import NumericShardStatistics


T = TypeVar("T", bound="ShardStatisticsPublicData")


@_attrs_define
class ShardStatisticsPublicData:
    """ """

    additional_properties: dict[str, Union["CategoricalShardStatistics", "NumericShardStatistics"]] = _attrs_field(
        init=False, factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        from ..models.numeric_shard_statistics import NumericShardStatistics

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            if isinstance(prop, NumericShardStatistics):
                field_dict[prop_name] = prop.to_dict()
            else:
                field_dict[prop_name] = prop.to_dict()

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.categorical_shard_statistics import CategoricalShardStatistics
        from ..models.numeric_shard_statistics import NumericShardStatistics

        d = dict(src_dict)
        shard_statistics_public_data = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():

            def _parse_additional_property(
                data: object,
            ) -> Union["CategoricalShardStatistics", "NumericShardStatistics"]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    additional_property_type_0 = NumericShardStatistics.from_dict(data)

                    return additional_property_type_0
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                additional_property_type_1 = CategoricalShardStatistics.from_dict(data)

                return additional_property_type_1

            additional_property = _parse_additional_property(prop_dict)

            additional_properties[prop_name] = additional_property

        shard_statistics_public_data.additional_properties = additional_properties
        return shard_statistics_public_data

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Union["CategoricalShardStatistics", "NumericShardStatistics"]:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Union["CategoricalShardStatistics", "NumericShardStatistics"]) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
