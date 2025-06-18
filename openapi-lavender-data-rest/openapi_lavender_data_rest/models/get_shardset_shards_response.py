from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.shard_public import ShardPublic


T = TypeVar("T", bound="GetShardsetShardsResponse")


@_attrs_define
class GetShardsetShardsResponse:
    """
    Attributes:
        shards (list['ShardPublic']):
        total (int):
    """

    shards: list["ShardPublic"]
    total: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        shards = []
        for shards_item_data in self.shards:
            shards_item = shards_item_data.to_dict()
            shards.append(shards_item)

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "shards": shards,
                "total": total,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.shard_public import ShardPublic

        d = dict(src_dict)
        shards = []
        _shards = d.pop("shards")
        for shards_item_data in _shards:
            shards_item = ShardPublic.from_dict(shards_item_data)

            shards.append(shards_item)

        total = d.pop("total")

        get_shardset_shards_response = cls(
            shards=shards,
            total=total,
        )

        get_shardset_shards_response.additional_properties = d
        return get_shardset_shards_response

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
