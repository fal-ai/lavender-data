from abc import ABC, abstractmethod

from .abc import Registry


class Filter(ABC):
    name: str

    @abstractmethod
    def filter(self, sample: dict) -> bool:
        raise NotImplementedError

    def __call__(self, sample: dict) -> bool:
        return self.filter(sample)


class FilterRegistry(Registry[Filter]):
    pass


@FilterRegistry.register("default")
class DefaultFilter(Filter):
    def filter(self, sample: dict) -> bool:
        return True
