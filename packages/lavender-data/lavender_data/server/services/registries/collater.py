from abc import ABC, abstractmethod

from .abc import Registry

try:
    from torch.utils.data import default_collate
except ImportError:
    default_collate = lambda samples: {
        k: [sample[k] for sample in samples] for k in samples[0].keys()
    }


class Collater(ABC):
    name: str

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def collate(self, samples: list[dict]) -> dict:
        raise NotImplementedError

    def __call__(self, samples: list[dict]) -> dict:
        return self.collate(samples)


class CollaterRegistry(Registry[Collater]):
    pass


@CollaterRegistry.register("default")
class DefaultCollater(Collater):
    def collate(self, samples: list[dict]) -> dict:
        return default_collate(samples)
