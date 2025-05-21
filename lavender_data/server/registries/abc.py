import inspect
from abc import ABC
from typing_extensions import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class FuncSpec(BaseModel):
    name: str
    args: list[tuple[str, str]]


class Registry(ABC, Generic[T]):
    def __init_subclass__(cls):
        cls._classes: dict[str, type[T]] = {}
        cls._func_specs: dict[str, FuncSpec] = {}
        cls._instances: dict[str, T] = {}

    @classmethod
    def register(cls, name: str, _class: T):
        _class.name = name
        cls._classes[name] = _class
        cls._func_specs[name] = FuncSpec(
            name=name,
            args=[
                (param.name, param.annotation.__name__)
                for param in inspect.signature(
                    getattr(_class, cls._func_name)
                ).parameters.values()
                if param.name != "self"
            ][1:],
        )

    @classmethod
    def initialize(cls):
        for name, _class in cls._classes.items():
            cls._instances[name] = _class()

    @classmethod
    def get(cls, name: str) -> T:
        if name not in cls._instances:
            raise ValueError(f"{cls.__name__} {name} not found")
        return cls._instances[name]

    @classmethod
    def all(cls) -> list[str]:
        return list(cls._classes.keys())

    @classmethod
    def specs(cls) -> list[FuncSpec]:
        return list(cls._func_specs.values())
