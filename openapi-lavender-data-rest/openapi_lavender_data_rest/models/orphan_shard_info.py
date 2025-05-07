from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.orphan_shard_info_columns import OrphanShardInfoColumns


T = TypeVar("T", bound="OrphanShardInfo")


@_attrs_define
class OrphanShardInfo:
    """
    Attributes:
        samples (int):
        location (str):
        format_ (str):
        filesize (int):
        columns (OrphanShardInfoColumns):
    """

    samples: int
    location: str
    format_: str
    filesize: int
    columns: "OrphanShardInfoColumns"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        samples = self.samples

        location = self.location

        format_ = self.format_

        filesize = self.filesize

        columns = self.columns.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "samples": samples,
                "location": location,
                "format": format_,
                "filesize": filesize,
                "columns": columns,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.orphan_shard_info_columns import OrphanShardInfoColumns

        d = dict(src_dict)
        samples = d.pop("samples")

        location = d.pop("location")

        format_ = d.pop("format")

        filesize = d.pop("filesize")

        columns = OrphanShardInfoColumns.from_dict(d.pop("columns"))

        orphan_shard_info = cls(
            samples=samples,
            location=location,
            format_=format_,
            filesize=filesize,
            columns=columns,
        )

        orphan_shard_info.additional_properties = d
        return orphan_shard_info

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
