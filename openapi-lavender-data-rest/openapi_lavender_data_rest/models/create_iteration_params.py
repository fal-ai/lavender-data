from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.iteration_categorizer import IterationCategorizer
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
        categorizer (Union['IterationCategorizer', None, Unset]):
        collater (Union['IterationCollater', None, Unset]):
        preprocessors (Union[None, Unset, list['IterationPreprocessor']]):
        shuffle (Union[None, Unset, bool]):
        shuffle_seed (Union[None, Unset, int]):
        shuffle_block_size (Union[None, Unset, int]):
        batch_size (Union[None, Unset, int]):
        replication_pg (Union[None, Unset, list[list[int]]]):
        rank (Union[None, Unset, int]):
        world_size (Union[None, Unset, int]):
        wait_participant_threshold (Union[None, Unset, float]):
        cluster_sync (Union[None, Unset, bool]):
    """

    dataset_id: str
    shardsets: Union[None, Unset, list[str]] = UNSET
    filters: Union[None, Unset, list["IterationFilter"]] = UNSET
    categorizer: Union["IterationCategorizer", None, Unset] = UNSET
    collater: Union["IterationCollater", None, Unset] = UNSET
    preprocessors: Union[None, Unset, list["IterationPreprocessor"]] = UNSET
    shuffle: Union[None, Unset, bool] = UNSET
    shuffle_seed: Union[None, Unset, int] = UNSET
    shuffle_block_size: Union[None, Unset, int] = UNSET
    batch_size: Union[None, Unset, int] = UNSET
    replication_pg: Union[None, Unset, list[list[int]]] = UNSET
    rank: Union[None, Unset, int] = UNSET
    world_size: Union[None, Unset, int] = UNSET
    wait_participant_threshold: Union[None, Unset, float] = UNSET
    cluster_sync: Union[None, Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.iteration_categorizer import IterationCategorizer
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

        categorizer: Union[None, Unset, dict[str, Any]]
        if isinstance(self.categorizer, Unset):
            categorizer = UNSET
        elif isinstance(self.categorizer, IterationCategorizer):
            categorizer = self.categorizer.to_dict()
        else:
            categorizer = self.categorizer

        collater: Union[None, Unset, dict[str, Any]]
        if isinstance(self.collater, Unset):
            collater = UNSET
        elif isinstance(self.collater, IterationCollater):
            collater = self.collater.to_dict()
        else:
            collater = self.collater

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

        rank: Union[None, Unset, int]
        if isinstance(self.rank, Unset):
            rank = UNSET
        else:
            rank = self.rank

        world_size: Union[None, Unset, int]
        if isinstance(self.world_size, Unset):
            world_size = UNSET
        else:
            world_size = self.world_size

        wait_participant_threshold: Union[None, Unset, float]
        if isinstance(self.wait_participant_threshold, Unset):
            wait_participant_threshold = UNSET
        else:
            wait_participant_threshold = self.wait_participant_threshold

        cluster_sync: Union[None, Unset, bool]
        if isinstance(self.cluster_sync, Unset):
            cluster_sync = UNSET
        else:
            cluster_sync = self.cluster_sync

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
        if categorizer is not UNSET:
            field_dict["categorizer"] = categorizer
        if collater is not UNSET:
            field_dict["collater"] = collater
        if preprocessors is not UNSET:
            field_dict["preprocessors"] = preprocessors
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
        if rank is not UNSET:
            field_dict["rank"] = rank
        if world_size is not UNSET:
            field_dict["world_size"] = world_size
        if wait_participant_threshold is not UNSET:
            field_dict["wait_participant_threshold"] = wait_participant_threshold
        if cluster_sync is not UNSET:
            field_dict["cluster_sync"] = cluster_sync

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.iteration_categorizer import IterationCategorizer
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

        def _parse_categorizer(data: object) -> Union["IterationCategorizer", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                categorizer_type_0 = IterationCategorizer.from_dict(data)

                return categorizer_type_0
            except:  # noqa: E722
                pass
            return cast(Union["IterationCategorizer", None, Unset], data)

        categorizer = _parse_categorizer(d.pop("categorizer", UNSET))

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

        def _parse_rank(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        rank = _parse_rank(d.pop("rank", UNSET))

        def _parse_world_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        world_size = _parse_world_size(d.pop("world_size", UNSET))

        def _parse_wait_participant_threshold(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        wait_participant_threshold = _parse_wait_participant_threshold(d.pop("wait_participant_threshold", UNSET))

        def _parse_cluster_sync(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        cluster_sync = _parse_cluster_sync(d.pop("cluster_sync", UNSET))

        create_iteration_params = cls(
            dataset_id=dataset_id,
            shardsets=shardsets,
            filters=filters,
            categorizer=categorizer,
            collater=collater,
            preprocessors=preprocessors,
            shuffle=shuffle,
            shuffle_seed=shuffle_seed,
            shuffle_block_size=shuffle_block_size,
            batch_size=batch_size,
            replication_pg=replication_pg,
            rank=rank,
            world_size=world_size,
            wait_participant_threshold=wait_participant_threshold,
            cluster_sync=cluster_sync,
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
