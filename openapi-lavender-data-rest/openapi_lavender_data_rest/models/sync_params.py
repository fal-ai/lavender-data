from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.api_key_base import ApiKeyBase
    from ..models.dataset_base import DatasetBase
    from ..models.dataset_column_base import DatasetColumnBase
    from ..models.iteration_base import IterationBase
    from ..models.iteration_shardset_link import IterationShardsetLink
    from ..models.shard_base import ShardBase
    from ..models.shardset_base import ShardsetBase


T = TypeVar("T", bound="SyncParams")


@_attrs_define
class SyncParams:
    """
    Attributes:
        datasets (list['DatasetBase']):
        dataset_columns (list['DatasetColumnBase']):
        shardsets (list['ShardsetBase']):
        shards (list['ShardBase']):
        iterations (list['IterationBase']):
        iteration_shardset_links (list['IterationShardsetLink']):
        api_keys (list['ApiKeyBase']):
    """

    datasets: list["DatasetBase"]
    dataset_columns: list["DatasetColumnBase"]
    shardsets: list["ShardsetBase"]
    shards: list["ShardBase"]
    iterations: list["IterationBase"]
    iteration_shardset_links: list["IterationShardsetLink"]
    api_keys: list["ApiKeyBase"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        datasets = []
        for datasets_item_data in self.datasets:
            datasets_item = datasets_item_data.to_dict()
            datasets.append(datasets_item)

        dataset_columns = []
        for dataset_columns_item_data in self.dataset_columns:
            dataset_columns_item = dataset_columns_item_data.to_dict()
            dataset_columns.append(dataset_columns_item)

        shardsets = []
        for shardsets_item_data in self.shardsets:
            shardsets_item = shardsets_item_data.to_dict()
            shardsets.append(shardsets_item)

        shards = []
        for shards_item_data in self.shards:
            shards_item = shards_item_data.to_dict()
            shards.append(shards_item)

        iterations = []
        for iterations_item_data in self.iterations:
            iterations_item = iterations_item_data.to_dict()
            iterations.append(iterations_item)

        iteration_shardset_links = []
        for iteration_shardset_links_item_data in self.iteration_shardset_links:
            iteration_shardset_links_item = iteration_shardset_links_item_data.to_dict()
            iteration_shardset_links.append(iteration_shardset_links_item)

        api_keys = []
        for api_keys_item_data in self.api_keys:
            api_keys_item = api_keys_item_data.to_dict()
            api_keys.append(api_keys_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "datasets": datasets,
                "dataset_columns": dataset_columns,
                "shardsets": shardsets,
                "shards": shards,
                "iterations": iterations,
                "iteration_shardset_links": iteration_shardset_links,
                "api_keys": api_keys,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_key_base import ApiKeyBase
        from ..models.dataset_base import DatasetBase
        from ..models.dataset_column_base import DatasetColumnBase
        from ..models.iteration_base import IterationBase
        from ..models.iteration_shardset_link import IterationShardsetLink
        from ..models.shard_base import ShardBase
        from ..models.shardset_base import ShardsetBase

        d = dict(src_dict)
        datasets = []
        _datasets = d.pop("datasets")
        for datasets_item_data in _datasets:
            datasets_item = DatasetBase.from_dict(datasets_item_data)

            datasets.append(datasets_item)

        dataset_columns = []
        _dataset_columns = d.pop("dataset_columns")
        for dataset_columns_item_data in _dataset_columns:
            dataset_columns_item = DatasetColumnBase.from_dict(dataset_columns_item_data)

            dataset_columns.append(dataset_columns_item)

        shardsets = []
        _shardsets = d.pop("shardsets")
        for shardsets_item_data in _shardsets:
            shardsets_item = ShardsetBase.from_dict(shardsets_item_data)

            shardsets.append(shardsets_item)

        shards = []
        _shards = d.pop("shards")
        for shards_item_data in _shards:
            shards_item = ShardBase.from_dict(shards_item_data)

            shards.append(shards_item)

        iterations = []
        _iterations = d.pop("iterations")
        for iterations_item_data in _iterations:
            iterations_item = IterationBase.from_dict(iterations_item_data)

            iterations.append(iterations_item)

        iteration_shardset_links = []
        _iteration_shardset_links = d.pop("iteration_shardset_links")
        for iteration_shardset_links_item_data in _iteration_shardset_links:
            iteration_shardset_links_item = IterationShardsetLink.from_dict(iteration_shardset_links_item_data)

            iteration_shardset_links.append(iteration_shardset_links_item)

        api_keys = []
        _api_keys = d.pop("api_keys")
        for api_keys_item_data in _api_keys:
            api_keys_item = ApiKeyBase.from_dict(api_keys_item_data)

            api_keys.append(api_keys_item)

        sync_params = cls(
            datasets=datasets,
            dataset_columns=dataset_columns,
            shardsets=shardsets,
            shards=shards,
            iterations=iterations,
            iteration_shardset_links=iteration_shardset_links,
            api_keys=api_keys,
        )

        sync_params.additional_properties = d
        return sync_params

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
