from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.iteration_collater import IterationCollater
    from ..models.iteration_filter import IterationFilter
    from ..models.iteration_preprocessor import IterationPreprocessor


T = TypeVar("T", bound="CreateIterationParams")


@_attrs_define
class CreateIterationParams:
    """
    Attributes:
        dataset_id (str):
        shardsets (Union[None, Unset, list[str]]):
        filters (Union[None, Unset, list['IterationFilter']]):
        preprocessors (Union[None, Unset, list['IterationPreprocessor']]):
        collater (Union['IterationCollater', None, Unset]):
        shuffle (Union[None, Unset, bool]):
        shuffle_seed (Union[None, Unset, int]):
        shuffle_block_size (Union[None, Unset, int]):
        batch_size (Union[None, Unset, int]):
        replication_pg (Union[None, Unset, list[list[int]]]):
    """

    dataset_id: str
    shardsets: Union[None, Unset, list[str]] = UNSET
    filters: Union[None, Unset, list["IterationFilter"]] = UNSET
    preprocessors: Union[None, Unset, list["IterationPreprocessor"]] = UNSET
    collater: Union["IterationCollater", None, Unset] = UNSET
    shuffle: Union[None, Unset, bool] = UNSET
    shuffle_seed: Union[None, Unset, int] = UNSET
    shuffle_block_size: Union[None, Unset, int] = UNSET
    batch_size: Union[None, Unset, int] = UNSET
    replication_pg: Union[None, Unset, list[list[int]]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.iteration_collater import IterationCollater

        dataset_id = self.dataset_id

        shardsets: Union[None, Unset, list[str]]
        if isinstance(self.shardsets, Unset):
            shardsets = UNSET
        elif isinstance(self.shardsets, list):
            shardsets = self.shardsets

        else:
            shardsets = self.shardsets

        filters: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.filters, Unset):
            filters = UNSET
        elif isinstance(self.filters, list):
            filters = []
            for filters_type_0_item_data in self.filters:
                filters_type_0_item = filters_type_0_item_data.to_dict()
                filters.append(filters_type_0_item)

        else:
            filters = self.filters

        preprocessors: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.preprocessors, Unset):
            preprocessors = UNSET
        elif isinstance(self.preprocessors, list):
            preprocessors = []
            for preprocessors_type_0_item_data in self.preprocessors:
                preprocessors_type_0_item = preprocessors_type_0_item_data.to_dict()
                preprocessors.append(preprocessors_type_0_item)

        else:
            preprocessors = self.preprocessors

        collater: Union[None, Unset, dict[str, Any]]
        if isinstance(self.collater, Unset):
            collater = UNSET
        elif isinstance(self.collater, IterationCollater):
            collater = self.collater.to_dict()
        else:
            collater = self.collater

        shuffle: Union[None, Unset, bool]
        if isinstance(self.shuffle, Unset):
            shuffle = UNSET
        else:
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

        batch_size: Union[None, Unset, int]
        if isinstance(self.batch_size, Unset):
            batch_size = UNSET
        else:
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
            }
        )
        if shardsets is not UNSET:
            field_dict["shardsets"] = shardsets
        if filters is not UNSET:
            field_dict["filters"] = filters
        if preprocessors is not UNSET:
            field_dict["preprocessors"] = preprocessors
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
        from ..models.iteration_collater import IterationCollater
        from ..models.iteration_filter import IterationFilter
        from ..models.iteration_preprocessor import IterationPreprocessor

        d = dict(src_dict)
        dataset_id = d.pop("dataset_id")

        def _parse_shardsets(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                shardsets_type_0 = cast(list[str], data)

                return shardsets_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        shardsets = _parse_shardsets(d.pop("shardsets", UNSET))

        def _parse_filters(data: object) -> Union[None, Unset, list["IterationFilter"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                filters_type_0 = []
                _filters_type_0 = data
                for filters_type_0_item_data in _filters_type_0:
                    filters_type_0_item = IterationFilter.from_dict(filters_type_0_item_data)

                    filters_type_0.append(filters_type_0_item)

                return filters_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["IterationFilter"]], data)

        filters = _parse_filters(d.pop("filters", UNSET))

        def _parse_preprocessors(data: object) -> Union[None, Unset, list["IterationPreprocessor"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                preprocessors_type_0 = []
                _preprocessors_type_0 = data
                for preprocessors_type_0_item_data in _preprocessors_type_0:
                    preprocessors_type_0_item = IterationPreprocessor.from_dict(preprocessors_type_0_item_data)

                    preprocessors_type_0.append(preprocessors_type_0_item)

                return preprocessors_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["IterationPreprocessor"]], data)

        preprocessors = _parse_preprocessors(d.pop("preprocessors", UNSET))

        def _parse_collater(data: object) -> Union["IterationCollater", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                collater_type_0 = IterationCollater.from_dict(data)

                return collater_type_0
            except:  # noqa: E722
                pass
            return cast(Union["IterationCollater", None, Unset], data)

        collater = _parse_collater(d.pop("collater", UNSET))

        def _parse_shuffle(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        shuffle = _parse_shuffle(d.pop("shuffle", UNSET))

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

        def _parse_batch_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        batch_size = _parse_batch_size(d.pop("batch_size", UNSET))

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

        create_iteration_params = cls(
            dataset_id=dataset_id,
            shardsets=shardsets,
            filters=filters,
            preprocessors=preprocessors,
            collater=collater,
            shuffle=shuffle,
            shuffle_seed=shuffle_seed,
            shuffle_block_size=shuffle_block_size,
            batch_size=batch_size,
            replication_pg=replication_pg,
        )

        create_iteration_params.additional_properties = d
        return create_iteration_params

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
