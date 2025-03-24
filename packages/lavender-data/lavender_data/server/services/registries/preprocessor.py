from abc import ABC, abstractmethod

from .abc import Registry


class Preprocessor(ABC):
    name: str

    @abstractmethod
    def process(self, batch: dict) -> dict:
        raise NotImplementedError

    def __call__(self, batch: dict) -> dict:
        return self.process(batch)


class PreprocessorRegistry(Registry[Preprocessor]):
    pass


@PreprocessorRegistry.register("default")
class DefaultPreprocessor(Preprocessor):
    def process(self, batch: dict) -> dict:
        return batch
