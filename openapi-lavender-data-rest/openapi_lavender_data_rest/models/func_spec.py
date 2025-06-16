from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="FuncSpec")


@_attrs_define
class FuncSpec:
    """
    Attributes:
        registry (str):
        name (str):
        args (list[list[str]]):
        md5 (str):
    """

    registry: str
    name: str
    args: list[list[str]]
    md5: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        registry = self.registry

        name = self.name

        args = []
        for args_item_data in self.args:
            args_item = []
            for args_item_item_data in args_item_data:
                args_item_item: str
                args_item_item = args_item_item_data
                args_item.append(args_item_item)

            args.append(args_item)

        md5 = self.md5

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "registry": registry,
                "name": name,
                "args": args,
                "md5": md5,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        registry = d.pop("registry")

        name = d.pop("name")

        args = []
        _args = d.pop("args")
        for args_item_data in _args:
            args_item = []
            _args_item = args_item_data
            for args_item_item_data in _args_item:

                def _parse_args_item_item(data: object) -> str:
                    return cast(str, data)

                args_item_item = _parse_args_item_item(args_item_item_data)

                args_item.append(args_item_item)

            args.append(args_item)

        md5 = d.pop("md5")

        func_spec = cls(
            registry=registry,
            name=name,
            args=args,
            md5=md5,
        )

        func_spec.additional_properties = d
        return func_spec

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
