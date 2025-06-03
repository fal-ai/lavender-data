from abc import ABC, abstractmethod

from .abc import Registry


class CollaterRegistry(Registry["Collater"]):
    _func_name: str = "collate"


class Collater(ABC):
    def __init_subclass__(cls, **kwargs):
        cls.name = kwargs.pop("name", getattr(cls, "name", cls.__name__))
        CollaterRegistry.register(cls.name, cls)

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def collate(self, samples: list[dict], **kwargs) -> dict:
        raise NotImplementedError
