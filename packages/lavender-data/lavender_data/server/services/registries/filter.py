from abc import ABC, abstractmethod

from .abc import Registry


class FilterRegistry(Registry["Filter"]):
    pass


class Filter(ABC):
    def __init_subclass__(cls, **kwargs):
        cls.name = kwargs.pop("name", getattr(cls, "name", cls.__name__))
        FilterRegistry.register(cls.name, cls)

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def filter(self, sample: dict, **kwargs) -> bool:
        raise NotImplementedError
