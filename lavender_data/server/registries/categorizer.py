from abc import ABC, abstractmethod

from .abc import Registry


class CategorizerRegistry(Registry["Categorizer"]):
    _func_name: str = "categorize"


class Categorizer(ABC):
    def __init_subclass__(cls, **kwargs):
        cls.name = kwargs.pop("name", getattr(cls, "name", cls.__name__))
        CategorizerRegistry.register(cls.name, cls)

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def categorize(self, sample: dict, **kwargs) -> str:
        raise NotImplementedError
