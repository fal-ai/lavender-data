from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateShardParams")


@_attrs_define
class CreateShardParams:
    """
    Attributes:
        location (str):
        filesize (int):
        samples (int):
        format_ (str):
        index (int):
        overwrite (Union[Unset, bool]):  Default: False.
    """

    location: str
    filesize: int
    samples: int
    format_: str
    index: int
    overwrite: Union[Unset, bool] = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        location = self.location

        filesize = self.filesize

        samples = self.samples

        format_ = self.format_

        index = self.index

        overwrite = self.overwrite

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "location": location,
                "filesize": filesize,
                "samples": samples,
                "format": format_,
                "index": index,
            }
        )
        if overwrite is not UNSET:
            field_dict["overwrite"] = overwrite

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        location = d.pop("location")

        filesize = d.pop("filesize")

        samples = d.pop("samples")

        format_ = d.pop("format")

        index = d.pop("index")

        overwrite = d.pop("overwrite", UNSET)

        create_shard_params = cls(
            location=location,
            filesize=filesize,
            samples=samples,
            format_=format_,
            index=index,
            overwrite=overwrite,
        )

        create_shard_params.additional_properties = d
        return create_shard_params

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
