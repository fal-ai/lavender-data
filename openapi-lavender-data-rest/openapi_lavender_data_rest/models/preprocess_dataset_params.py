from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.iteration_preprocessor import IterationPreprocessor


T = TypeVar("T", bound="PreprocessDatasetParams")


@_attrs_define
class PreprocessDatasetParams:
    """
    Attributes:
        shardset_location (str):
        preprocessors (list['IterationPreprocessor']):
        export_columns (list[str]):
        batch_size (int):
        source_shardset_ids (Union[None, Unset, list[str]]):
        overwrite (Union[Unset, bool]):  Default: False.
    """

    shardset_location: str
    preprocessors: list["IterationPreprocessor"]
    export_columns: list[str]
    batch_size: int
    source_shardset_ids: Union[None, Unset, list[str]] = UNSET
    overwrite: Union[Unset, bool] = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        shardset_location = self.shardset_location

        preprocessors = []
        for preprocessors_item_data in self.preprocessors:
            preprocessors_item = preprocessors_item_data.to_dict()
            preprocessors.append(preprocessors_item)

        export_columns = self.export_columns

        batch_size = self.batch_size

        source_shardset_ids: Union[None, Unset, list[str]]
        if isinstance(self.source_shardset_ids, Unset):
            source_shardset_ids = UNSET
        elif isinstance(self.source_shardset_ids, list):
            source_shardset_ids = self.source_shardset_ids

        else:
            source_shardset_ids = self.source_shardset_ids

        overwrite = self.overwrite

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "shardset_location": shardset_location,
                "preprocessors": preprocessors,
                "export_columns": export_columns,
                "batch_size": batch_size,
            }
        )
        if source_shardset_ids is not UNSET:
            field_dict["source_shardset_ids"] = source_shardset_ids
        if overwrite is not UNSET:
            field_dict["overwrite"] = overwrite

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.iteration_preprocessor import IterationPreprocessor

        d = dict(src_dict)
        shardset_location = d.pop("shardset_location")

        preprocessors = []
        _preprocessors = d.pop("preprocessors")
        for preprocessors_item_data in _preprocessors:
            preprocessors_item = IterationPreprocessor.from_dict(preprocessors_item_data)

            preprocessors.append(preprocessors_item)

        export_columns = cast(list[str], d.pop("export_columns"))

        batch_size = d.pop("batch_size")

        def _parse_source_shardset_ids(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                source_shardset_ids_type_0 = cast(list[str], data)

                return source_shardset_ids_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        source_shardset_ids = _parse_source_shardset_ids(d.pop("source_shardset_ids", UNSET))

        overwrite = d.pop("overwrite", UNSET)

        preprocess_dataset_params = cls(
            shardset_location=shardset_location,
            preprocessors=preprocessors,
            export_columns=export_columns,
            batch_size=batch_size,
            source_shardset_ids=source_shardset_ids,
            overwrite=overwrite,
        )

        preprocess_dataset_params.additional_properties = d
        return preprocess_dataset_params

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
