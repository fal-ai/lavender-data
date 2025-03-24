import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dataset_public import DatasetPublic
    from ..models.shardset_with_shards import ShardsetWithShards


T = TypeVar("T", bound="GetIterationResponse")


@_attrs_define
class GetIterationResponse:
    """
    Attributes:
        dataset_id (str):
        created_at (datetime.datetime):
        dataset (DatasetPublic):
        shardsets (list['ShardsetWithShards']):
        id (Union[Unset, str]):
        total (Union[Unset, int]):  Default: 0.
        filter_ (Union[None, Unset, str]):
        preprocessor (Union[None, Unset, str]):
        collater (Union[None, Unset, str]):
        shuffle (Union[Unset, bool]):  Default: False.
        shuffle_seed (Union[None, Unset, int]):
        shuffle_block_size (Union[None, Unset, int]):
        batch_size (Union[Unset, int]):  Default: 0.
        replication_pg (Union[None, Unset, list[list[int]]]):
    """

    dataset_id: str
    created_at: datetime.datetime
    dataset: "DatasetPublic"
    shardsets: list["ShardsetWithShards"]
    id: Union[Unset, str] = UNSET
    total: Union[Unset, int] = 0
    filter_: Union[None, Unset, str] = UNSET
    preprocessor: Union[None, Unset, str] = UNSET
    collater: Union[None, Unset, str] = UNSET
    shuffle: Union[Unset, bool] = False
    shuffle_seed: Union[None, Unset, int] = UNSET
    shuffle_block_size: Union[None, Unset, int] = UNSET
    batch_size: Union[Unset, int] = 0
    replication_pg: Union[None, Unset, list[list[int]]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_id = self.dataset_id

        created_at = self.created_at.isoformat()

        dataset = self.dataset.to_dict()

        shardsets = []
        for shardsets_item_data in self.shardsets:
            shardsets_item = shardsets_item_data.to_dict()
            shardsets.append(shardsets_item)

        id = self.id

        total = self.total

        filter_: Union[None, Unset, str]
        if isinstance(self.filter_, Unset):
            filter_ = UNSET
        else:
            filter_ = self.filter_

        preprocessor: Union[None, Unset, str]
        if isinstance(self.preprocessor, Unset):
            preprocessor = UNSET
        else:
            preprocessor = self.preprocessor

        collater: Union[None, Unset, str]
        if isinstance(self.collater, Unset):
            collater = UNSET
        else:
            collater = self.collater

        shuffle = self.shuffle

        shuffle_seed: Union[None, Unset, int]
        if isinstance(self.shuffle_seed, Unset):
            shuffle_seed = UNSET
        else:
            shuffle_seed = self.shuffle_seed

        shuffle_block_size: Union[None, Unset, int]
        if isinstance(self.shuffle_block_size, Unset):
            shuffle_block_size = UNSET
        else:
            shuffle_block_size = self.shuffle_block_size

        batch_size = self.batch_size

        replication_pg: Union[None, Unset, list[list[int]]]
        if isinstance(self.replication_pg, Unset):
            replication_pg = UNSET
        elif isinstance(self.replication_pg, list):
            replication_pg = []
            for replication_pg_type_0_item_data in self.replication_pg:
                replication_pg_type_0_item = replication_pg_type_0_item_data

                replication_pg.append(replication_pg_type_0_item)

        else:
            replication_pg = self.replication_pg

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_id": dataset_id,
                "created_at": created_at,
                "dataset": dataset,
                "shardsets": shardsets,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if total is not UNSET:
            field_dict["total"] = total
        if filter_ is not UNSET:
            field_dict["filter"] = filter_
        if preprocessor is not UNSET:
            field_dict["preprocessor"] = preprocessor
        if collater is not UNSET:
            field_dict["collater"] = collater
        if shuffle is not UNSET:
            field_dict["shuffle"] = shuffle
        if shuffle_seed is not UNSET:
            field_dict["shuffle_seed"] = shuffle_seed
        if shuffle_block_size is not UNSET:
            field_dict["shuffle_block_size"] = shuffle_block_size
        if batch_size is not UNSET:
            field_dict["batch_size"] = batch_size
        if replication_pg is not UNSET:
            field_dict["replication_pg"] = replication_pg

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_public import DatasetPublic
        from ..models.shardset_with_shards import ShardsetWithShards

        d = dict(src_dict)
        dataset_id = d.pop("dataset_id")

        created_at = isoparse(d.pop("created_at"))

        dataset = DatasetPublic.from_dict(d.pop("dataset"))

        shardsets = []
        _shardsets = d.pop("shardsets")
        for shardsets_item_data in _shardsets:
            shardsets_item = ShardsetWithShards.from_dict(shardsets_item_data)

            shardsets.append(shardsets_item)

        id = d.pop("id", UNSET)

        total = d.pop("total", UNSET)

        def _parse_filter_(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        filter_ = _parse_filter_(d.pop("filter", UNSET))

        def _parse_preprocessor(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        preprocessor = _parse_preprocessor(d.pop("preprocessor", UNSET))

        def _parse_collater(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        collater = _parse_collater(d.pop("collater", UNSET))

        shuffle = d.pop("shuffle", UNSET)

        def _parse_shuffle_seed(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        shuffle_seed = _parse_shuffle_seed(d.pop("shuffle_seed", UNSET))

        def _parse_shuffle_block_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        shuffle_block_size = _parse_shuffle_block_size(d.pop("shuffle_block_size", UNSET))

        batch_size = d.pop("batch_size", UNSET)

        def _parse_replication_pg(data: object) -> Union[None, Unset, list[list[int]]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                replication_pg_type_0 = []
                _replication_pg_type_0 = data
                for replication_pg_type_0_item_data in _replication_pg_type_0:
                    replication_pg_type_0_item = cast(list[int], replication_pg_type_0_item_data)

                    replication_pg_type_0.append(replication_pg_type_0_item)

                return replication_pg_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[list[int]]], data)

        replication_pg = _parse_replication_pg(d.pop("replication_pg", UNSET))

        get_iteration_response = cls(
            dataset_id=dataset_id,
            created_at=created_at,
            dataset=dataset,
            shardsets=shardsets,
            id=id,
            total=total,
            filter_=filter_,
            preprocessor=preprocessor,
            collater=collater,
            shuffle=shuffle,
            shuffle_seed=shuffle_seed,
            shuffle_block_size=shuffle_block_size,
            batch_size=batch_size,
            replication_pg=replication_pg,
        )

        get_iteration_response.additional_properties = d
        return get_iteration_response

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
