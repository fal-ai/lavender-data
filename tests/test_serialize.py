import unittest

import torch
import numpy as np

from lavender_data.serialize import serialize_sample, deserialize_sample


class TestSerializeSample(unittest.TestCase):
    def test_serialize_sample(self):
        sample = {
            "int": 1,
            "float": 0.1,
            "list": [2, 3],
            "list_of_dict": [{"a": 1}, {"b": 2}],
            "list_of_list": [[1, 2], [3, 4]],
            "dict": {"d": 4},
            "dict_of_dict": {"e": {"f": 5}},
            "dict_of_list": {"g": [6, 7]},
            "string": "hello",
            "bytes": b"\x00\x01\x02\x03\x04",
            "ndarray": np.array([[1, 2, 3], [4, 5, 6]]),
            "tensor": torch.tensor([[1, 2, 3], [4, 5, 6]]),
            "none": None,
        }
        serialized = serialize_sample(sample)

        self.assertEqual(type(serialized), bytes)

        deserialized = deserialize_sample(serialized)

        self.assertEqual(len(sample), len(deserialized))

        for key in sample.keys():
            if key == "ndarray" or key == "tensor":
                self.assertTrue((sample[key] == deserialized[key]).all())
            else:
                self.assertEqual(sample[key], deserialized[key])
