from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.shard_statistics_public_data import ShardStatisticsPublicData


T = TypeVar("T", bound="ShardStatisticsPublic")


@_attrs_define
class ShardStatisticsPublic:
    """
    Attributes:
        shard_id (str):
        data (ShardStatisticsPublicData):
    """

    shard_id: str
    data: "ShardStatisticsPublicData"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        shard_id = self.shard_id

        data = self.data.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "shard_id": shard_id,
                "data": data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.shard_statistics_public_data import ShardStatisticsPublicData

        d = dict(src_dict)
        shard_id = d.pop("shard_id")

        data = ShardStatisticsPublicData.from_dict(d.pop("data"))

        shard_statistics_public = cls(
            shard_id=shard_id,
            data=data,
        )

        shard_statistics_public.additional_properties = d
        return shard_statistics_public

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
