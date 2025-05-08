import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="DatasetPublic")


@_attrs_define
class DatasetPublic:
    """
    Attributes:
        name (str):
        created_at (datetime.datetime):
        id (Union[Unset, str]):
        uid_column_name (Union[Unset, str]):  Default: 'uid'.
    """

    name: str
    created_at: datetime.datetime
    id: Union[Unset, str] = UNSET
    uid_column_name: Union[Unset, str] = "uid"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        created_at = self.created_at.isoformat()

        id = self.id

        uid_column_name = self.uid_column_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "created_at": created_at,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if uid_column_name is not UNSET:
            field_dict["uid_column_name"] = uid_column_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        created_at = isoparse(d.pop("created_at"))

        id = d.pop("id", UNSET)

        uid_column_name = d.pop("uid_column_name", UNSET)

        dataset_public = cls(
            name=name,
            created_at=created_at,
            id=id,
            uid_column_name=uid_column_name,
        )

        dataset_public.additional_properties = d
        return dataset_public

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
