import json
from abc import ABC
from typing_extensions import Generic, TypeVar, Any

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
            return _class

        return decorator

    @classmethod
    def get(cls, name: str, params: dict[str, Any] = {}) -> T:
        if name not in cls.classes:
            raise ValueError(f"{cls.__name__} {name} not found")
        reg_class = cls.classes[name]
        key = f"{name}:{json.dumps(params)}"
        if key not in cls.instances:
            cls.instances[key] = reg_class(**params)
        return cls.instances[key]

    @classmethod
    def list(cls) -> list[str]:
        return list(cls.classes.keys())
