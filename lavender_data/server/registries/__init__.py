import sys
import importlib.util
from pathlib import Path
from typing import Optional
from lavender_data.logging import get_logger

from .abc import Registry, FuncSpec
from .collater import CollaterRegistry, Collater
from .filter import FilterRegistry, Filter
from .categorizer import CategorizerRegistry, Categorizer
from .preprocessor import PreprocessorRegistry, Preprocessor

__all__ = [
    "setup_registries",
    "CollaterRegistry",
    "Collater",
    "FilterRegistry",
    "Filter",
    "CategorizerRegistry",
    "Categorizer",
    "PreprocessorRegistry",
    "Preprocessor",
    "FuncSpec",
]


def import_from_directory(directory: str):
    logger = get_logger(__name__)
    for file in Path(directory).glob("*.py"):
        before = {
            "filter": FilterRegistry.all(),
            "categorizer": CategorizerRegistry.all(),
            "collater": CollaterRegistry.all(),
            "preprocessor": PreprocessorRegistry.all(),
        }

        mod_name = file.stem
        spec = importlib.util.spec_from_file_location(mod_name, file)
        mod = importlib.util.module_from_spec(spec)

        sys.modules[f"lavender_data.server.registries.{mod_name}"] = mod
        spec.loader.exec_module(mod)

        after = {
            "filter": FilterRegistry.all(),
            "categorizer": CategorizerRegistry.all(),
            "collater": CollaterRegistry.all(),
            "preprocessor": PreprocessorRegistry.all(),
        }
        diff = {
            key: list(set(after[key]) - set(before[key]))
            for key in ["preprocessor", "filter", "collater", "categorizer"]
            if set(after[key]) - set(before[key])
        }
        logger.info(f"Imported {file}: {diff}")


def setup_registries(modules_dir: Optional[str] = None):
    if modules_dir:
        import_from_directory(modules_dir)

    FilterRegistry.initialize()
    CategorizerRegistry.initialize()
    CollaterRegistry.initialize()
    PreprocessorRegistry.initialize()
