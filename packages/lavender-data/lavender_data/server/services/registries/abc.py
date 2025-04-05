from abc import ABC
from typing_extensions import Generic, TypeVar

T = TypeVar("T")


class Registry(ABC, Generic[T]):
    def __init_subclass__(cls):
        cls.classes: dict[str, T] = {}
        cls.instances: dict[str, T] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(_class: T):
            _class.name = name
            cls.classes[name] = _class
            cls.get(name)
            return _class

        return decorator

    @classmethod
    def get(cls, name: str) -> T:
        if name not in cls.classes:
            raise ValueError(f"{cls.__name__} {name} not found")
        reg_class = cls.classes[name]
        if name not in cls.instances:
            cls.instances[name] = reg_class()
        return cls.instances[name]

    @classmethod
    def list(cls) -> list[str]:
        return list(cls.classes.keys())
