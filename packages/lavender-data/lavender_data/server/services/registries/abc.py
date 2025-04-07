from abc import ABC
from typing_extensions import Generic, TypeVar

T = TypeVar("T")


class Registry(ABC, Generic[T]):
    def __init_subclass__(cls):
        cls._instances: dict[str, T] = {}

    @classmethod
    def register(cls, name: str, _class: T):
        _class.name = name
        cls._instances[name] = _class()

    @classmethod
    def get(cls, name: str) -> T:
        if name not in cls._instances:
            raise ValueError(f"{cls.__name__} {name} not found")
        return cls._instances[name]

    @classmethod
    def list(cls) -> list[str]:
        return list(cls._instances.keys())
