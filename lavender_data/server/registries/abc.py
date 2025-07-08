import inspect
import hashlib
from abc import ABC
from typing import Optional
from typing_extensions import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class FuncSpec(BaseModel):
    registry: str
    name: str
    args: list[tuple[str, str]]
    md5: str


def _get_md5(_class: type[T]) -> str:
    try:
        source = inspect.getsource(_class)
    except Exception as e:
        source = _class.__name__
    return hashlib.md5(source.encode()).hexdigest()


class Registry(ABC, Generic[T]):
    def __init_subclass__(cls):
        cls._classes: dict[str, type[T]] = {}
        cls._func_specs: dict[str, FuncSpec] = {}
        cls._instances: dict[str, T] = {}

    @classmethod
    def register(cls, name: str, _class: type[T]):
        _class.name = name
        cls._classes[name] = _class
        cls._func_specs[name] = FuncSpec(
            registry=cls.__name__,
            name=name,
            args=[
                (param.name, param.annotation.__name__)
                for param in inspect.signature(
                    getattr(_class, cls._func_name)
                ).parameters.values()
                if param.name != "self"
            ][1:],
            md5=_get_md5(_class),
        )

    @classmethod
    def initialize(cls, name: Optional[str] = None):
        for _name, _class in cls._classes.items():
            if name is not None and _name != name:
                continue
            if _name in cls._instances and cls._func_specs[_name].md5 == _get_md5(
                _class
            ):
                continue
            cls._instances[_name] = _class()

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
