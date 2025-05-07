from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.dataset_column_public import DatasetColumnPublic
    from ..models.dataset_public import DatasetPublic
    from ..models.preview_dataset_response_samples_item import PreviewDatasetResponseSamplesItem


T = TypeVar("T", bound="PreviewDatasetResponse")


@_attrs_define
class PreviewDatasetResponse:
    """
    Attributes:
        dataset (DatasetPublic):
        columns (list['DatasetColumnPublic']):
        samples (list['PreviewDatasetResponseSamplesItem']):
        total (int):
    """

    dataset: "DatasetPublic"
    columns: list["DatasetColumnPublic"]
    samples: list["PreviewDatasetResponseSamplesItem"]
    total: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset = self.dataset.to_dict()

        columns = []
        for columns_item_data in self.columns:
            columns_item = columns_item_data.to_dict()
            columns.append(columns_item)

        samples = []
        for samples_item_data in self.samples:
            samples_item = samples_item_data.to_dict()
            samples.append(samples_item)

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset": dataset,
                "columns": columns,
                "samples": samples,
                "total": total,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_column_public import DatasetColumnPublic
        from ..models.dataset_public import DatasetPublic
        from ..models.preview_dataset_response_samples_item import PreviewDatasetResponseSamplesItem

        d = dict(src_dict)
        dataset = DatasetPublic.from_dict(d.pop("dataset"))

        columns = []
        _columns = d.pop("columns")
        for columns_item_data in _columns:
            columns_item = DatasetColumnPublic.from_dict(columns_item_data)

            columns.append(columns_item)

        samples = []
        _samples = d.pop("samples")
        for samples_item_data in _samples:
            samples_item = PreviewDatasetResponseSamplesItem.from_dict(samples_item_data)

            samples.append(samples_item)

        total = d.pop("total")

        preview_dataset_response = cls(
            dataset=dataset,
            columns=columns,
            samples=samples,
            total=total,
        )

        preview_dataset_response.additional_properties = d
        return preview_dataset_response

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
