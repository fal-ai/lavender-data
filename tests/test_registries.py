import time
import unittest
import numpy as np
import sys

from lavender_data.server.registries.abc import Registry
from lavender_data.server.registries import (
    Preprocessor,
    PreprocessorRegistry,
    Filter,
    FilterRegistry,
    Collater,
    CollaterRegistry,
    Categorizer,
    CategorizerRegistry,
)


# Test registries
class TestRegistry(Registry["TestComponent"]):
    _func_name = "process"


class TestComponent:
    def __init_subclass__(cls, **kwargs):
        cls.name = kwargs.pop("name", getattr(cls, "name", cls.__name__))
        TestRegistry.register(cls.name, cls)

    def __init__(self, **kwargs):
        pass


if sys.version_info >= (3, 11):

    class TestComponent1(TestComponent, name="test1"):
        def process(self):
            return "test1_result"

    class TestComponent2(TestComponent, name="test2"):
        def process(self):
            return "test2_result"

    # Test preprocessors
    class MultiplyPreprocessor(Preprocessor, name="multiply"):
        def process(self, batch: dict, *, multiply: int = 1) -> dict:
            batch["multiplied"] = batch["value"] * multiply
            return batch

    class AddPreprocessor(Preprocessor, name="add"):
        def process(self, batch: dict, *, add: int = 1) -> dict:
            batch["added"] = batch["value"] + add
            return batch

    class SlowPreprocessor(Preprocessor, name="slow"):
        def process(self, batch: dict, *, wait: int = 1) -> dict:
            time.sleep(wait)
            return batch

    class AddAfterMultiplyPreprocessor(
        Preprocessor, name="add_after_multiply", depends_on=["multiply"]
    ):
        def process(self, batch: dict, *, add: int = 1) -> dict:
            batch["added"] = batch["multiplied"] + add
            return batch

    # Test filters
    class ModFilter(Filter, name="mod"):
        def filter(self, sample: dict, *, mod: int = 1) -> bool:
            return sample["value"] % mod == 0

    # Test categorizers
    class AspectRatioCategorizer(Categorizer, name="aspect_ratio"):
        def categorize(self, sample: dict) -> str:
            return f"{sample['width']}x{sample['height']}"

    # Test collaters
    class CountCollater(Collater, name="count"):
        def collate(self, samples: list[dict]) -> dict:
            return {"count": len(samples)}

else:

    class TestComponent1(TestComponent):
        name = "test1"

        def process(self):
            return "test1_result"

    class TestComponent2(TestComponent):
        name = "test2"

        def process(self):
            return "test2_result"

    # Test preprocessors
    class MultiplyPreprocessor(Preprocessor):
        name = "multiply"

        def process(self, batch: dict, *, multiply: int = 1) -> dict:
            batch["multiplied"] = batch["value"] * multiply
            return batch

    class AddPreprocessor(Preprocessor):
        name = "add"

        def process(self, batch: dict, *, add: int = 1) -> dict:
            batch["added"] = batch["value"] + add
            return batch

    class SlowPreprocessor(Preprocessor):
        name = "slow"

        def process(self, batch: dict, *, wait: int = 1) -> dict:
            time.sleep(wait)
            return batch

    class AddAfterMultiplyPreprocessor(
        Preprocessor,
    ):
        name = "add_after_multiply"
        depends_on = ["multiply"]

        def process(self, batch: dict, *, add: int = 1) -> dict:
            batch["added"] = batch["multiplied"] + add
            return batch

    # Test filters
    class ModFilter(Filter):
        name = "mod"

        def filter(self, sample: dict, *, mod: int = 1) -> bool:
            return sample["value"] % mod == 0

    # Test categorizers
    class AspectRatioCategorizer(Categorizer):
        name = "aspect_ratio"

        def categorize(self, sample: dict) -> str:
            return f"{sample['width']}x{sample['height']}"

    # Test collaters
    class CountCollater(Collater):
        name = "count"

        def collate(self, samples: list[dict]) -> dict:
            return {"count": len(samples)}


class RegistriesTest(unittest.TestCase):
    def setUp(self):
        TestRegistry.initialize()
        PreprocessorRegistry.initialize()
        FilterRegistry.initialize()
        CategorizerRegistry.initialize()
        CollaterRegistry.initialize()

    def test_base_registry(self):
        # Test registration
        self.assertEqual(len(TestRegistry.all()), 2)
        self.assertIn("test1", TestRegistry.all())
        self.assertIn("test2", TestRegistry.all())

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
        self.assertIn("multiply", PreprocessorRegistry.all())

        # Test getting preprocessors
        preprocessor1 = PreprocessorRegistry.get("multiply")
        self.assertIsInstance(preprocessor1, MultiplyPreprocessor)

        batch = {"value": np.array([1, 2, 3])}
        processed_batch = preprocessor1.process(batch, multiply=2)
        self.assertEqual(processed_batch["multiplied"].tolist(), [2, 4, 6])

    def test_filter_registry(self):
        # Test registration
        self.assertIn("mod", FilterRegistry.all())

        # Test getting filters
        filter1 = FilterRegistry.get("mod")
        self.assertIsInstance(filter1, ModFilter)

        samples = [{"value": 1}, {"value": 2}, {"value": 3}]
        for sample in samples:
            if sample["value"] % 2 == 0:
                self.assertTrue(filter1.filter(sample, mod=2))
            else:
                self.assertFalse(filter1.filter(sample, mod=2))

    def test_categorizer_registry(self):
        # Test registration
        self.assertIn("aspect_ratio", CategorizerRegistry.all())

        # Test getting categorizers
        categorizer1 = CategorizerRegistry.get("aspect_ratio")
        self.assertIsInstance(categorizer1, AspectRatioCategorizer)

        self.assertEqual(
            categorizer1.categorize({"width": 1280, "height": 720}), "1280x720"
        )
        self.assertEqual(
            categorizer1.categorize({"width": 1920, "height": 1080}), "1920x1080"
        )

    def test_collater_registry(self):
        # Test registration
        self.assertIn("count", CollaterRegistry.all())

        # Test getting collaters
        collater1 = CollaterRegistry.get("count")
        self.assertIsInstance(collater1, CountCollater)

        samples = [{"sample": 1}, {"sample": 2}]
        collated = collater1.collate(samples)
        self.assertEqual(collated.get("count"), 2)

    def test_preprocessor_registry_process(self):
        batch = {"value": np.array([1, 2, 3])}

        # Concurrency
        self.assertIn("slow", PreprocessorRegistry.all())
        start = time.time()
        PreprocessorRegistry.process(
            [
                ("slow", {"wait": 1}),
                ("slow", {"wait": 1}),
                ("slow", {"wait": 1}),
                ("slow", {"wait": 1}),
            ],
            batch,
            max_workers=10,
        )
        end = time.time()
        self.assertLessEqual(abs(end - start) - 1, 0.01)

        # depends_on
        self.assertIn("add_after_multiply", PreprocessorRegistry.all())

        self.assertRaises(
            ValueError,
            lambda: PreprocessorRegistry.process(
                [("add_after_multiply", {"add": 1})], batch
            ),
        )

        PreprocessorRegistry.process(
            [
                ("multiply", {"multiply": 2}),
                ("add_after_multiply", {"add": 1}),
            ],
            batch,
        )
        self.assertEqual(batch["added"].tolist(), [3, 5, 7])
