import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dataset_column_public import DatasetColumnPublic
    from ..models.shard_public import ShardPublic


T = TypeVar("T", bound="ShardsetWithShards")


@_attrs_define
class ShardsetWithShards:
    """
    Attributes:
        dataset_id (str):
        location (str):
        created_at (datetime.datetime):
        shard_count (int):
        total_samples (int):
        shards (list['ShardPublic']):
        columns (list['DatasetColumnPublic']):
        id (Union[Unset, str]):
        is_main (Union[Unset, bool]):  Default: False.
    """

    dataset_id: str
    location: str
    created_at: datetime.datetime
    shard_count: int
    total_samples: int
    shards: list["ShardPublic"]
    columns: list["DatasetColumnPublic"]
    id: Union[Unset, str] = UNSET
    is_main: Union[Unset, bool] = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_id = self.dataset_id

        location = self.location

        created_at = self.created_at.isoformat()

        shard_count = self.shard_count

        total_samples = self.total_samples

        shards = []
        for shards_item_data in self.shards:
            shards_item = shards_item_data.to_dict()
            shards.append(shards_item)

        columns = []
        for columns_item_data in self.columns:
            columns_item = columns_item_data.to_dict()
            columns.append(columns_item)

        id = self.id

        is_main = self.is_main

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_id": dataset_id,
                "location": location,
                "created_at": created_at,
                "shard_count": shard_count,
                "total_samples": total_samples,
                "shards": shards,
                "columns": columns,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if is_main is not UNSET:
            field_dict["is_main"] = is_main

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_column_public import DatasetColumnPublic
        from ..models.shard_public import ShardPublic

        d = dict(src_dict)
        dataset_id = d.pop("dataset_id")

        location = d.pop("location")

        created_at = isoparse(d.pop("created_at"))

        shard_count = d.pop("shard_count")

        total_samples = d.pop("total_samples")

        shards = []
        _shards = d.pop("shards")
        for shards_item_data in _shards:
            shards_item = ShardPublic.from_dict(shards_item_data)

            shards.append(shards_item)

        columns = []
        _columns = d.pop("columns")
        for columns_item_data in _columns:
            columns_item = DatasetColumnPublic.from_dict(columns_item_data)

            columns.append(columns_item)

        id = d.pop("id", UNSET)

        is_main = d.pop("is_main", UNSET)

        shardset_with_shards = cls(
            dataset_id=dataset_id,
            location=location,
            created_at=created_at,
            shard_count=shard_count,
            total_samples=total_samples,
            shards=shards,
            columns=columns,
            id=id,
            is_main=is_main,
        )

        shardset_with_shards.additional_properties = d
        return shardset_with_shards

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
