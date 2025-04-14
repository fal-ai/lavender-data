from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SyncShardsetStatus")


@_attrs_define
class SyncShardsetStatus:
    """
    Attributes:
        status (str):
        done_count (int):
        shard_count (int):
    """

    status: str
    done_count: int
    shard_count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        done_count = self.done_count

        shard_count = self.shard_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
                "done_count": done_count,
                "shard_count": shard_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        status = d.pop("status")

        done_count = d.pop("done_count")

        shard_count = d.pop("shard_count")

        sync_shardset_status = cls(
            status=status,
            done_count=done_count,
            shard_count=shard_count,
        )

        sync_shardset_status.additional_properties = d
        return sync_shardset_status

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
