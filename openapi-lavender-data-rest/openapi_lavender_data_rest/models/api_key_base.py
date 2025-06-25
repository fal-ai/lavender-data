import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="ApiKeyBase")


@_attrs_define
class ApiKeyBase:
    """
    Attributes:
        note (Union[None, str]):
        created_at (datetime.datetime):
        expires_at (Union[None, datetime.datetime]):
        last_accessed_at (Union[None, datetime.datetime]):
        id (Union[Unset, str]):
        secret (Union[Unset, str]):
        locked (Union[Unset, bool]):  Default: False.
    """

    note: Union[None, str]
    created_at: datetime.datetime
    expires_at: Union[None, datetime.datetime]
    last_accessed_at: Union[None, datetime.datetime]
    id: Union[Unset, str] = UNSET
    secret: Union[Unset, str] = UNSET
    locked: Union[Unset, bool] = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        note: Union[None, str]
        note = self.note

        created_at = self.created_at.isoformat()

        expires_at: Union[None, str]
        if isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        last_accessed_at: Union[None, str]
        if isinstance(self.last_accessed_at, datetime.datetime):
            last_accessed_at = self.last_accessed_at.isoformat()
        else:
            last_accessed_at = self.last_accessed_at

        id = self.id

        secret = self.secret

        locked = self.locked

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "note": note,
                "created_at": created_at,
                "expires_at": expires_at,
                "last_accessed_at": last_accessed_at,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if secret is not UNSET:
            field_dict["secret"] = secret
        if locked is not UNSET:
            field_dict["locked"] = locked

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_note(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        note = _parse_note(d.pop("note"))

        created_at = isoparse(d.pop("created_at"))

        def _parse_expires_at(data: object) -> Union[None, datetime.datetime]:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_at_type_0 = isoparse(data)

                return expires_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, datetime.datetime], data)

        expires_at = _parse_expires_at(d.pop("expires_at"))

        def _parse_last_accessed_at(data: object) -> Union[None, datetime.datetime]:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_accessed_at_type_0 = isoparse(data)

                return last_accessed_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, datetime.datetime], data)

        last_accessed_at = _parse_last_accessed_at(d.pop("last_accessed_at"))

        id = d.pop("id", UNSET)

        secret = d.pop("secret", UNSET)

        locked = d.pop("locked", UNSET)

        api_key_base = cls(
            note=note,
            created_at=created_at,
            expires_at=expires_at,
            last_accessed_at=last_accessed_at,
            id=id,
            secret=secret,
            locked=locked,
        )

        api_key_base.additional_properties = d
        return api_key_base

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
