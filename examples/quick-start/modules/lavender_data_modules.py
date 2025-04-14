from lavender_data.server import (
    Preprocessor,
    Filter,
    Collater,
)


class UidModFilter(Filter, name="uid_mod"):
    def filter(self, sample: dict, *, mod: int = 2) -> bool:
        return sample["uid"] % mod == 0


class PyListCollater(Collater, name="pylist"):
    def collate(self, samples: list[dict]) -> dict:
        return {
            "uid": [sample["uid"] for sample in samples],
            "text": [sample["text"] for sample in samples],
        }


class AppendNewColumn(Preprocessor, name="append_new_column"):
    def process(self, batch: dict) -> dict:
        import time

        time.sleep(2)
        batch["new_column"] = []
        for uid in batch["uid"]:
            batch["new_column"].append(f"{uid}_processed")
        return batch
