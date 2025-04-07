import unittest
import numpy as np

from lavender_data.server.services.registries.abc import Registry
from lavender_data.server.services.registries import (
    Preprocessor,
    PreprocessorRegistry,
    Filter,
    FilterRegistry,
    Collater,
    CollaterRegistry,
)


# Test registries
class TestRegistry(Registry["TestComponent"]):
    pass


class TestComponent:
    def __init_subclass__(cls, **kwargs):
        cls.name = kwargs.pop("name", getattr(cls, "name", cls.__name__))
        TestRegistry.register(cls.name, cls)

    def __init__(self, **kwargs):
        pass


class TestComponent1(TestComponent, name="test1"):
    def process(self):
        return "test1_result"


class TestComponent2(TestComponent, name="test2"):
    def process(self):
        return "test2_result"


# Test preprocessors
class CustomPreprocessor1(Preprocessor, name="multiply"):
    def process(self, batch: dict, *, multiply: int = 1) -> dict:
        batch["processed"] = batch["value"] * multiply
        return batch


# Test filters
class CustomFilter1(Filter, name="mod"):
    def filter(self, sample: dict, *, mod: int = 1) -> bool:
        return sample["value"] % mod == 0


# Test collaters
class CustomCollater1(Collater, name="count"):
    def collate(self, samples: list[dict]) -> dict:
        return {"count": len(samples)}


class RegistriesTest(unittest.TestCase):
    def test_base_registry(self):
        # Test registration
        self.assertEqual(len(TestRegistry.list()), 2)
        self.assertIn("test1", TestRegistry.list())
        self.assertIn("test2", TestRegistry.list())

        # Test getting components
        comp1 = TestRegistry.get("test1")
        self.assertIsInstance(comp1, TestComponent1)
        self.assertEqual(comp1.process(), "test1_result")

        comp2 = TestRegistry.get("test2")
        self.assertIsInstance(comp2, TestComponent2)
        self.assertEqual(comp2.process(), "test2_result")

        # Test error on non-existent component
        with self.assertRaises(ValueError):
            TestRegistry.get("non_existent")

    def test_preprocessor_registry(self):
        # Test registration
        self.assertIn("multiply", PreprocessorRegistry.list())

        # Test getting preprocessors
        preprocessor1 = PreprocessorRegistry.get("multiply")
        self.assertIsInstance(preprocessor1, CustomPreprocessor1)

        batch = {"value": np.array([1, 2, 3])}
        processed_batch = preprocessor1.process(batch, multiply=2)
        self.assertEqual(processed_batch["processed"].tolist(), [2, 4, 6])

    def test_filter_registry(self):
        # Test registration
        self.assertIn("mod", FilterRegistry.list())

        # Test getting filters
        filter1 = FilterRegistry.get("mod")
        self.assertIsInstance(filter1, CustomFilter1)

        samples = [{"value": 1}, {"value": 2}, {"value": 3}]
        for sample in samples:
            if sample["value"] % 2 == 0:
                self.assertTrue(filter1.filter(sample, mod=2))
            else:
                self.assertFalse(filter1.filter(sample, mod=2))

    def test_collater_registry(self):
        # Test registration
        self.assertIn("count", CollaterRegistry.list())
        self.assertIn("default", CollaterRegistry.list())  # Default collater

        # Test getting collaters
        collater1 = CollaterRegistry.get("count")
        self.assertIsInstance(collater1, CustomCollater1)

        samples = [{"sample": 1}, {"sample": 2}]
        collated = collater1.collate(samples)
        self.assertEqual(collated.get("count"), 2)
