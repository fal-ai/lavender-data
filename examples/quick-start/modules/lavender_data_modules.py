from lavender_data.server import (
    PreprocessorRegistry,
    Preprocessor,
    FilterRegistry,
    Filter,
    CollaterRegistry,
    Collater,
)


@FilterRegistry.register("uid_mod")
class UidModFilter(Filter):
    def filter(self, sample: dict, *, mod: int = 2) -> bool:
        return sample["uid"] % mod == 0


@CollaterRegistry.register("pylist")
class PyListCollater(Collater):
    def collate(self, samples: list[dict]) -> dict:
        return {
            "uid": [sample["uid"] for sample in samples],
            "text": [sample["text"] for sample in samples],
        }


@PreprocessorRegistry.register("append_new_column")
class AppendNewColumn(Preprocessor):
    def process(self, batch: dict) -> dict:
        batch["new_column"] = []
        for uid in batch["uid"]:
            batch["new_column"].append(f"{uid}_processed")
        return batch
