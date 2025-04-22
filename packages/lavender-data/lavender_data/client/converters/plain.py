from .abc import Converter


class PlainConverter(Converter):
    name = "plain"

    def transform(self, sample: dict) -> dict:
        return sample
