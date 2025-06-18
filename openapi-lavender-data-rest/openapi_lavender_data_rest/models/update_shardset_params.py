from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateShardsetParams")


@_attrs_define
class UpdateShardsetParams:
    """
    Attributes:
        is_main (Union[Unset, bool]):  Default: False.
    """

    is_main: Union[Unset, bool] = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_main = self.is_main

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if is_main is not UNSET:
            field_dict["is_main"] = is_main

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_main = d.pop("is_main", UNSET)

        update_shardset_params = cls(
            is_main=is_main,
        )

        update_shardset_params.additional_properties = d
        return update_shardset_params

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
