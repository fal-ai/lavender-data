import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="ShardsetPublic")


@_attrs_define
class ShardsetPublic:
    """
    Attributes:
        dataset_id (str):
        location (str):
        created_at (datetime.datetime):
        id (Union[Unset, str]):
        shard_count (Union[Unset, int]):  Default: 0.
        total_samples (Union[Unset, int]):  Default: 0.
    """

    dataset_id: str
    location: str
    created_at: datetime.datetime
    id: Union[Unset, str] = UNSET
    shard_count: Union[Unset, int] = 0
    total_samples: Union[Unset, int] = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_id = self.dataset_id

        location = self.location

        created_at = self.created_at.isoformat()

        id = self.id

        shard_count = self.shard_count

        total_samples = self.total_samples

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_id": dataset_id,
                "location": location,
                "created_at": created_at,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if shard_count is not UNSET:
            field_dict["shard_count"] = shard_count
        if total_samples is not UNSET:
            field_dict["total_samples"] = total_samples

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        dataset_id = d.pop("dataset_id")

        location = d.pop("location")

        created_at = isoparse(d.pop("created_at"))

        id = d.pop("id", UNSET)

        shard_count = d.pop("shard_count", UNSET)

        total_samples = d.pop("total_samples", UNSET)

        shardset_public = cls(
            dataset_id=dataset_id,
            location=location,
            created_at=created_at,
            id=id,
            shard_count=shard_count,
            total_samples=total_samples,
        )

        shardset_public.additional_properties = d
        return shardset_public

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
