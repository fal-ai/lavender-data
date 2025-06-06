from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.iteration_categorizer_params import IterationCategorizerParams


T = TypeVar("T", bound="IterationCategorizer")


@_attrs_define
class IterationCategorizer:
    """
    Attributes:
        name (str):
        params (IterationCategorizerParams):
    """

    name: str
    params: "IterationCategorizerParams"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        params = self.params.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "params": params,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.iteration_categorizer_params import IterationCategorizerParams

        d = dict(src_dict)
        name = d.pop("name")

        params = IterationCategorizerParams.from_dict(d.pop("params"))

        iteration_categorizer = cls(
            name=name,
            params=params,
        )

        iteration_categorizer.additional_properties = d
        return iteration_categorizer

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
