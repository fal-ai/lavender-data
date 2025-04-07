from abc import ABC, abstractmethod

from .abc import Registry


class PreprocessorRegistry(Registry["Preprocessor"]):
    pass


class Preprocessor(ABC):
    def __init_subclass__(cls, **kwargs):
        cls.name = kwargs.pop("name", getattr(cls, "name", cls.__name__))
        PreprocessorRegistry.register(cls.name, cls)

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def process(self, batch: dict, **kwargs) -> dict:
        raise NotImplementedError
