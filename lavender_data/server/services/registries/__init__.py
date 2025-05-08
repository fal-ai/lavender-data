import sys
import importlib.util
from pathlib import Path

from lavender_data.logging import get_logger

from .collater import CollaterRegistry, Collater
from .filter import FilterRegistry, Filter
from .preprocessor import PreprocessorRegistry, Preprocessor

__all__ = [
    "import_from_directory",
    "CollaterRegistry",
    "Collater",
    "FilterRegistry",
    "Filter",
    "PreprocessorRegistry",
    "Preprocessor",
]


def import_from_directory(directory: str):
    logger = get_logger(__name__)
    for file in Path(directory).glob("*.py"):
        before = {
            "preprocessor": PreprocessorRegistry.list(),
            "filter": FilterRegistry.list(),
            "collater": CollaterRegistry.list(),
        }

        mod_name = file.stem
        spec = importlib.util.spec_from_file_location(mod_name, file)
        mod = importlib.util.module_from_spec(spec)

        sys.modules[f"lavender_data.server.services.registries.{mod_name}"] = mod
        spec.loader.exec_module(mod)

        after = {
            "preprocessor": PreprocessorRegistry.list(),
            "filter": FilterRegistry.list(),
            "collater": CollaterRegistry.list(),
        }
        diff = {
            key: list(set(after[key]) - set(before[key]))
            for key in ["preprocessor", "filter", "collater"]
            if set(after[key]) - set(before[key])
        }
        logger.info(f"Imported {file}: {diff}")
