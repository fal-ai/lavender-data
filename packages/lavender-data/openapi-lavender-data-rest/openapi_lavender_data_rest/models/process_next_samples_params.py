from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.iteration_collater import IterationCollater
    from ..models.iteration_preprocessor import IterationPreprocessor
    from ..models.process_next_samples_params_samples_item import ProcessNextSamplesParamsSamplesItem


T = TypeVar("T", bound="ProcessNextSamplesParams")


@_attrs_define
class ProcessNextSamplesParams:
    """
    Attributes:
        current (int):
        indices (list[int]):
        samples (list['ProcessNextSamplesParamsSamplesItem']):
        batch_size (int):
        collater (Union['IterationCollater', None, Unset]):
        preprocessors (Union[None, Unset, list['IterationPreprocessor']]):
    """

    current: int
    indices: list[int]
    samples: list["ProcessNextSamplesParamsSamplesItem"]
    batch_size: int
    collater: Union["IterationCollater", None, Unset] = UNSET
    preprocessors: Union[None, Unset, list["IterationPreprocessor"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.iteration_collater import IterationCollater

        current = self.current

        indices = self.indices

        samples = []
        for samples_item_data in self.samples:
            samples_item = samples_item_data.to_dict()
            samples.append(samples_item)

        batch_size = self.batch_size

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "current": current,
                "indices": indices,
                "samples": samples,
                "batch_size": batch_size,
            }
        )
        if collater is not UNSET:
            field_dict["collater"] = collater
        if preprocessors is not UNSET:
            field_dict["preprocessors"] = preprocessors

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.iteration_collater import IterationCollater
        from ..models.iteration_preprocessor import IterationPreprocessor
        from ..models.process_next_samples_params_samples_item import ProcessNextSamplesParamsSamplesItem

        d = dict(src_dict)
        current = d.pop("current")

        indices = cast(list[int], d.pop("indices"))

        samples = []
        _samples = d.pop("samples")
        for samples_item_data in _samples:
            samples_item = ProcessNextSamplesParamsSamplesItem.from_dict(samples_item_data)

            samples.append(samples_item)

        batch_size = d.pop("batch_size")

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

        process_next_samples_params = cls(
            current=current,
            indices=indices,
            samples=samples,
            batch_size=batch_size,
            collater=collater,
            preprocessors=preprocessors,
        )

        process_next_samples_params.additional_properties = d
        return process_next_samples_params

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
