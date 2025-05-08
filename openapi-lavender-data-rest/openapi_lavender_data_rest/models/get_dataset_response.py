import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dataset_column_public import DatasetColumnPublic
    from ..models.shardset_public import ShardsetPublic


T = TypeVar("T", bound="GetDatasetResponse")


@_attrs_define
class GetDatasetResponse:
    """
    Attributes:
        name (str):
        created_at (datetime.datetime):
        columns (list['DatasetColumnPublic']):
        shardsets (list['ShardsetPublic']):
        id (Union[Unset, str]):
        uid_column_name (Union[Unset, str]):  Default: 'uid'.
    """

    name: str
    created_at: datetime.datetime
    columns: list["DatasetColumnPublic"]
    shardsets: list["ShardsetPublic"]
    id: Union[Unset, str] = UNSET
    uid_column_name: Union[Unset, str] = "uid"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        created_at = self.created_at.isoformat()

        columns = []
        for columns_item_data in self.columns:
            columns_item = columns_item_data.to_dict()
            columns.append(columns_item)

        shardsets = []
        for shardsets_item_data in self.shardsets:
            shardsets_item = shardsets_item_data.to_dict()
            shardsets.append(shardsets_item)

        id = self.id

        uid_column_name = self.uid_column_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "created_at": created_at,
                "columns": columns,
                "shardsets": shardsets,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if uid_column_name is not UNSET:
            field_dict["uid_column_name"] = uid_column_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_column_public import DatasetColumnPublic
        from ..models.shardset_public import ShardsetPublic

        d = dict(src_dict)
        name = d.pop("name")

        created_at = isoparse(d.pop("created_at"))

        columns = []
        _columns = d.pop("columns")
        for columns_item_data in _columns:
            columns_item = DatasetColumnPublic.from_dict(columns_item_data)

            columns.append(columns_item)

        shardsets = []
        _shardsets = d.pop("shardsets")
        for shardsets_item_data in _shardsets:
            shardsets_item = ShardsetPublic.from_dict(shardsets_item_data)

            shardsets.append(shardsets_item)

        id = d.pop("id", UNSET)

        uid_column_name = d.pop("uid_column_name", UNSET)

        get_dataset_response = cls(
            name=name,
            created_at=created_at,
            columns=columns,
            shardsets=shardsets,
            id=id,
            uid_column_name=uid_column_name,
        )

        get_dataset_response.additional_properties = d
        return get_dataset_response

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
