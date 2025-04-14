import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="ShardPublic")


@_attrs_define
class ShardPublic:
    """
    Attributes:
        shardset_id (str):
        location (str):
        format_ (str):
        created_at (datetime.datetime):
        id (Union[Unset, str]):
        filesize (Union[Unset, int]):  Default: 0.
        samples (Union[Unset, int]):  Default: 0.
        index (Union[Unset, int]):  Default: 0.
    """

    shardset_id: str
    location: str
    format_: str
    created_at: datetime.datetime
    id: Union[Unset, str] = UNSET
    filesize: Union[Unset, int] = 0
    samples: Union[Unset, int] = 0
    index: Union[Unset, int] = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        shardset_id = self.shardset_id

        location = self.location

        format_ = self.format_

        created_at = self.created_at.isoformat()

        id = self.id

        filesize = self.filesize

        samples = self.samples

        index = self.index

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "shardset_id": shardset_id,
                "location": location,
                "format": format_,
                "created_at": created_at,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if filesize is not UNSET:
            field_dict["filesize"] = filesize
        if samples is not UNSET:
            field_dict["samples"] = samples
        if index is not UNSET:
            field_dict["index"] = index

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        shardset_id = d.pop("shardset_id")

        location = d.pop("location")

        format_ = d.pop("format")

        created_at = isoparse(d.pop("created_at"))

        id = d.pop("id", UNSET)

        filesize = d.pop("filesize", UNSET)

        samples = d.pop("samples", UNSET)

        index = d.pop("index", UNSET)

        shard_public = cls(
            shardset_id=shardset_id,
            location=location,
            format_=format_,
            created_at=created_at,
            id=id,
            filesize=filesize,
            samples=samples,
            index=index,
        )

        shard_public.additional_properties = d
        return shard_public

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
