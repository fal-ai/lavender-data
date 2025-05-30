import sys
import time
import importlib.util
import hashlib
from pathlib import Path
from typing import Optional
from threading import Thread

from lavender_data.logging import get_logger

from .abc import FuncSpec, Registry
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

script_hashes = set()


def _group_by_registry(
    specs: list[FuncSpec], registries: list[Registry]
) -> dict[str, list[FuncSpec]]:
    d = {
        r.__name__: [a.name for a in specs if a.registry == r.__name__]
        for r in registries
    }
    return {k: v for k, v in d.items() if len(v) > 0}


def _import_from_directory(directory: str):
    global script_hashes
    # TODO unable to delete

    logger = get_logger(__name__)
    current_hashes = set()

    registries: list[Registry] = [
        FilterRegistry,
        CategorizerRegistry,
        CollaterRegistry,
        PreprocessorRegistry,
    ]

    before: list[FuncSpec] = []
    for registry in registries:
        before.extend(registry.specs())

    for file in Path(directory).glob("*.py"):
        with open(file, "rb") as f:
            script_hash = hashlib.sha256(f.read()).hexdigest()
            if script_hash in script_hashes:
                continue
            current_hashes.add(script_hash)

        mod_name = file.stem
        spec = importlib.util.spec_from_file_location(mod_name, file)
        mod = importlib.util.module_from_spec(spec)

        sys.modules[mod_name] = mod

        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            logger.error(f"Error importing {mod_name}: {e}")
            continue

    after: list[FuncSpec] = []
    for registry in registries:
        after.extend(registry.specs())

    added: list[FuncSpec] = []
    modified: list[FuncSpec] = []
    for a in after:
        if a.name not in [b.name for b in before]:
            added.append(a)
            continue

        for b in before:
            if a.name == b.name and a.md5 != b.md5:
                modified.append(a)
                break

    if len(added) > 0 or len(modified) > 0:
        logger.info(f"Imported {file}")
        if len(added) > 0:
            logger.info(f"added {_group_by_registry(added, registries)}")
        if len(modified) > 0:
            logger.info(f"modified {_group_by_registry(modified, registries)}")

    script_hashes = current_hashes


def _watch_modules(modules_dir: str, interval: int):
    while True:
        _import_from_directory(modules_dir)
        time.sleep(interval)


def setup_registries(modules_dir: Optional[str] = None, interval: int = 10):
    if modules_dir:
        _import_from_directory(modules_dir)

        if interval > 0:
            Thread(
                target=_watch_modules,
                args=(modules_dir, interval),
                daemon=True,
            ).start()
