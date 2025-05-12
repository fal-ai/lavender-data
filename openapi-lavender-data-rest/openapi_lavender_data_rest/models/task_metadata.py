import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.task_metadata_kwargs import TaskMetadataKwargs
    from ..models.task_status import TaskStatus


T = TypeVar("T", bound="TaskMetadata")


@_attrs_define
class TaskMetadata:
    """
    Attributes:
        uid (str):
        name (str):
        start_time (datetime.datetime):
        kwargs (TaskMetadataKwargs):
        status (Union['TaskStatus', None, Unset]):
    """

    uid: str
    name: str
    start_time: datetime.datetime
    kwargs: "TaskMetadataKwargs"
    status: Union["TaskStatus", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.task_status import TaskStatus

        uid = self.uid

        name = self.name

        start_time = self.start_time.isoformat()

        kwargs = self.kwargs.to_dict()

        status: Union[None, Unset, dict[str, Any]]
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, TaskStatus):
            status = self.status.to_dict()
        else:
            status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "uid": uid,
                "name": name,
                "start_time": start_time,
                "kwargs": kwargs,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.task_metadata_kwargs import TaskMetadataKwargs
        from ..models.task_status import TaskStatus

        d = dict(src_dict)
        uid = d.pop("uid")

        name = d.pop("name")

        start_time = isoparse(d.pop("start_time"))

        kwargs = TaskMetadataKwargs.from_dict(d.pop("kwargs"))

        def _parse_status(data: object) -> Union["TaskStatus", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                status_type_0 = TaskStatus.from_dict(data)

                return status_type_0
            except:  # noqa: E722
                pass
            return cast(Union["TaskStatus", None, Unset], data)

        status = _parse_status(d.pop("status", UNSET))

        task_metadata = cls(
            uid=uid,
            name=name,
            start_time=start_time,
            kwargs=kwargs,
            status=status,
        )

        task_metadata.additional_properties = d
        return task_metadata

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
