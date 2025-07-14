from typing import Optional, Any
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from abc import ABC, abstractmethod

from .abc import Registry


class PreprocessorRegistry(Registry["Preprocessor"]):
    _func_name: str = "process"

    @classmethod
    def process(
        cls,
        preprocessors: list[tuple[str, dict[str, Any]]],
        batch: dict,
        *,
        max_workers: Optional[int] = None,
    ):
        executor = ThreadPoolExecutor(max_workers)

        current = [(cls.get(p[0]), p[1]) for p in preprocessors]
        executed: list[str] = []
        while len(current) > 0:
            execute_this_round = []
            _current = []
            for preprocessor, params in current:
                deps = [d for d in preprocessor.depends_on]

                # preprocessor is ready to execute
                if (
                    # it has no dependencies
                    len(preprocessor.depends_on) == 0
                    # or all dependencies have been executed
                    or all(d in executed for d in deps)
                ):
                    execute_this_round.append((preprocessor, params))
                else:
                    # unprocessable if some dependencies are not met
                    for dep in deps:
                        if not dep in [p[0].name for p in current]:
                            raise ValueError(
                                f"Preprocessor '{preprocessor.name}' depends on {deps} but '{dep}' is not included in {[p[0].name for p in current]}."
                            )
                    _current.append((preprocessor, params))

            futures: list[Future] = []
            for preprocessor, params in execute_this_round:
                # execute preprocessors in parallel, if they are independent with each other
                futures.append(executor.submit(preprocessor.process, batch, **params))
                executed.append(preprocessor.name)

            for future in as_completed(futures):
                batch.update(future.result())

            current = _current

        executor.shutdown(wait=True)

        return batch


class Preprocessor(ABC):
    name: str
    depends_on: list[str]

    def __init_subclass__(cls, *, name: str = None, depends_on: list[str] = None):
        cls.name = name or getattr(cls, "name", cls.__name__)
        cls.depends_on = depends_on or getattr(cls, "depends_on", [])
        PreprocessorRegistry.register(cls.name, cls)

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def process(self, batch: dict, **kwargs) -> dict:
        raise NotImplementedError
