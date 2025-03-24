import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="DatasetColumnPublic")


@_attrs_define
class DatasetColumnPublic:
    """
    Attributes:
        dataset_id (str):
        shardset_id (str):
        name (str):
        type_ (str):
        created_at (datetime.datetime):
        id (Union[Unset, str]):
        description (Union[None, Unset, str]):
    """

    dataset_id: str
    shardset_id: str
    name: str
    type_: str
    created_at: datetime.datetime
    id: Union[Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_id = self.dataset_id

        shardset_id = self.shardset_id

        name = self.name

        type_ = self.type_

        created_at = self.created_at.isoformat()

        id = self.id

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_id": dataset_id,
                "shardset_id": shardset_id,
                "name": name,
                "type": type_,
                "created_at": created_at,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        dataset_id = d.pop("dataset_id")

        shardset_id = d.pop("shardset_id")

        name = d.pop("name")

        type_ = d.pop("type")

        created_at = isoparse(d.pop("created_at"))

        id = d.pop("id", UNSET)

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        dataset_column_public = cls(
            dataset_id=dataset_id,
            shardset_id=shardset_id,
            name=name,
            type_=type_,
            created_at=created_at,
            id=id,
            description=description,
        )

        dataset_column_public.additional_properties = d
        return dataset_column_public

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
