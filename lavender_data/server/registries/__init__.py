import sys
import tempfile
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
    "import_from_code",
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

registries: list[Registry] = [
    FilterRegistry,
    CategorizerRegistry,
    CollaterRegistry,
    PreprocessorRegistry,
]


def _group_by_registry(
    specs: list[FuncSpec], registries: list[Registry]
) -> dict[str, list[FuncSpec]]:
    d = {
        r.__name__: [a.name for a in specs if a.registry == r.__name__]
        for r in registries
    }
    return {k: v for k, v in d.items() if len(v) > 0}


def _import_from_file(filepath: Path, force: bool = False):
    with open(filepath, "rb") as f:
        script_hash = hashlib.md5(f.read()).hexdigest()
        if script_hash in script_hashes and not force:
            return None

    mod_name = filepath.stem
    spec = importlib.util.spec_from_file_location(mod_name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod

    spec.loader.exec_module(mod)
    return script_hash


def _import_from_directory(directory: str):
    global script_hashes
    # TODO unable to delete

    logger = get_logger(__name__)

    before: list[FuncSpec] = []
    for registry in registries:
        before.extend(registry.specs())

    current_hashes = set()
    for file in Path(directory).glob("*.py"):
        try:
            script_hash = _import_from_file(file)
        except Exception as e:
            logger.error(f"Error importing {file}: {e}")
            continue

        if script_hash:
            current_hashes.add(script_hash)
    script_hashes = current_hashes

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

    for f in [*added, *modified]:
        r = next(r for r in registries if r.__name__ == f.registry)
        r.initialize(f.name)

    if len(added) > 0 or len(modified) > 0:
        logger.info(f"Imported {file}")
        if len(added) > 0:
            logger.info(f"added {_group_by_registry(added, registries)}")
        if len(modified) > 0:
            logger.info(f"modified {_group_by_registry(modified, registries)}")


def import_from_code(code: str):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(code)
        f.flush()
        _import_from_file(Path(f.name))


def _watch_modules(modules_dir: str, interval: int):
    while True:
        _import_from_directory(modules_dir)
        time.sleep(interval)


def setup_registries(modules_dir: Optional[str] = None, interval: int = 10):
    _import_from_directory(Path(__file__).parent / "built_in")
    if modules_dir:
        _import_from_directory(modules_dir)

        if interval > 0:
            Thread(
                target=_watch_modules,
                args=(modules_dir, interval),
                daemon=True,
            ).start()
    else:
        for registry in registries:
            registry.initialize()
