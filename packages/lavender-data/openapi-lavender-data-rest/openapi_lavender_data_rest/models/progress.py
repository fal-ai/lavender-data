from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.in_progress_index import InProgressIndex


T = TypeVar("T", bound="Progress")


@_attrs_define
class Progress:
    """
    Attributes:
        total (int):
        current (int):
        inprogress (list['InProgressIndex']):
        completed (int):
        filtered (int):
        failed (int):
    """

    total: int
    current: int
    inprogress: list["InProgressIndex"]
    completed: int
    filtered: int
    failed: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total = self.total

        current = self.current

        inprogress = []
        for inprogress_item_data in self.inprogress:
            inprogress_item = inprogress_item_data.to_dict()
            inprogress.append(inprogress_item)

        completed = self.completed

        filtered = self.filtered

        failed = self.failed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total": total,
                "current": current,
                "inprogress": inprogress,
                "completed": completed,
                "filtered": filtered,
                "failed": failed,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.in_progress_index import InProgressIndex

        d = dict(src_dict)
        total = d.pop("total")

        current = d.pop("current")

        inprogress = []
        _inprogress = d.pop("inprogress")
        for inprogress_item_data in _inprogress:
            inprogress_item = InProgressIndex.from_dict(inprogress_item_data)

            inprogress.append(inprogress_item)

        completed = d.pop("completed")

        filtered = d.pop("filtered")

        failed = d.pop("failed")

        progress = cls(
            total=total,
            current=current,
            inprogress=inprogress,
            completed=completed,
            filtered=filtered,
            failed=failed,
        )

        progress.additional_properties = d
        return progress

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
