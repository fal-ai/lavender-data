import json

from lavender_data.serialize import serialize_ndarray

from .abc import Converter

try:
    import PIL.Image
    import numpy as np
except ImportError:
    pass


class WebDatasetConverter(Converter):
    name = "webdataset"

    default_uid_column_name = "__key__"

    def transform(self, sample: dict) -> dict:
        if not PIL or not np:
            raise ImportError(
                "PIL and numpy are required to convert WebDataset to Lavender Data"
            )

        _json = sample.pop("json", None)

        if isinstance(_json, bytes) or isinstance(_json, str):
            try:
                _json = json.loads(_json)
            except Exception as e:
                _json = {}
        elif isinstance(_json, dict):
            pass
        else:
            _json = {}

        for k, v in sample.items():
            if isinstance(v, PIL.Image.Image):
                sample[k] = serialize_ndarray(np.array(v))

        try:
            # sample.pop("__key__")
            sample.pop("__url__")
            sample.pop("__local_path__")
        except KeyError:
            pass
        return {
            **_json,
            **sample,
        }
