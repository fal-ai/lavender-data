from abc import ABC, abstractmethod

from .abc import Registry

try:
    from torch.utils.data import default_collate
except ImportError:
    default_collate = lambda samples: {
        k: [sample[k] for sample in samples] for k in samples[0].keys()
    }


class CollaterRegistry(Registry["Collater"]):
    pass


class Collater(ABC):
    def __init_subclass__(cls, **kwargs):
        cls.name = kwargs.pop("name", getattr(cls, "name", cls.__name__))
        CollaterRegistry.register(cls.name, cls)

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def collate(self, samples: list[dict], **kwargs) -> dict:
        raise NotImplementedError


class DefaultCollater(Collater, name="default"):
    def collate(self, samples: list[dict]) -> dict:
        return default_collate(samples)
