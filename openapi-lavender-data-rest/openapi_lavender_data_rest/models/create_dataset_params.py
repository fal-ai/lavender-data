from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateDatasetParams")


@_attrs_define
class CreateDatasetParams:
    """
    Attributes:
        name (str):
        uid_column_name (Union[None, Unset, str]):
    """

    name: str
    uid_column_name: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        uid_column_name: Union[None, Unset, str]
        if isinstance(self.uid_column_name, Unset):
            uid_column_name = UNSET
        else:
            uid_column_name = self.uid_column_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if uid_column_name is not UNSET:
            field_dict["uid_column_name"] = uid_column_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        def _parse_uid_column_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        uid_column_name = _parse_uid_column_name(d.pop("uid_column_name", UNSET))

        create_dataset_params = cls(
            name=name,
            uid_column_name=uid_column_name,
        )

        create_dataset_params.additional_properties = d
        return create_dataset_params

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
