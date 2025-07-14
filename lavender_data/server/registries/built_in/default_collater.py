from lavender_data.server.registries.collater import Collater


class DefaultCollater(Collater):
    name = "default"

    def __init__(self):
        try:
            from torch.utils.data import default_collate
        except ImportError:
            default_collate = lambda samples: {
                k: [sample[k] for sample in samples] for k in samples[0].keys()
            }
        self.default_collate = default_collate

    def collate(self, samples: list[dict]) -> dict:
        return self.default_collate(samples)
