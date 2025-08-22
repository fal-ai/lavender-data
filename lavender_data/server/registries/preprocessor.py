from abc import ABC, abstractmethod

from .abc import Registry


class PreprocessorRegistry(Registry["Preprocessor"]):
    _func_name: str = "process"


class Preprocessor(ABC):
    name: str
    depends_on: list[str]

    def __init_subclass__(cls, *, name: str = None, depends_on: list[str] = None):
        cls.name = name or getattr(cls, "name", cls.__name__)
        cls.depends_on = depends_on or getattr(cls, "depends_on", [])
        PreprocessorRegistry.register(cls.name, cls)

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def process(self, batch: dict, **kwargs) -> dict:
        raise NotImplementedError
