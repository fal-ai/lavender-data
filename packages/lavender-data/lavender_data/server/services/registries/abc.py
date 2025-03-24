from abc import ABC
from typing_extensions import Generic, TypeVar


T = TypeVar("T")


class Registry(ABC, Generic[T]):
    def __init_subclass__(cls):
        cls._items: dict[str, T] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(_item: T):
            _item.name = name
            cls._items[name] = _item()
            return _item

        return decorator

    @classmethod
    def get(cls, name: str) -> T:
        if name not in cls._items:
            raise ValueError(f"{cls.__name__} {name} not found")
        return cls._items[name]

    @classmethod
    def list(cls) -> list[str]:
        return list(cls._items.keys())
