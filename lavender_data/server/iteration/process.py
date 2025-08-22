import ujson as json
from typing import Optional
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import HTTPException
from pydantic import BaseModel

try:
    import torch
except ImportError:
    torch = None

from lavender_data.logging import get_logger
from lavender_data.server.background_worker import pool_task
from lavender_data.server.db.models import (
    IterationPreprocessor,
    IterationCollater,
)
from lavender_data.server.reader import (
    get_reader_instance,
    GlobalSampleIndex,
    JoinMethod,
    InnerJoinSampleInsufficient,
)
from lavender_data.server.registries import (
    PreprocessorRegistry,
    CollaterRegistry,
    Preprocessor,
)


class CollateSamplesParams(BaseModel):
    current: int
    global_sample_indices: list[GlobalSampleIndex]
    samples: Optional[list[dict]] = None
    collater: Optional[IterationCollater] = None


class ProcessNextSamplesParams(CollateSamplesParams):
    preprocessors: Optional[list[IterationPreprocessor]] = None
    batch_size: int


class ProcessNextSamplesException(Exception):
    msg: str
    tb: str
    current: int
    global_sample_indices: list[GlobalSampleIndex]

    def __init__(
        self, e: Exception, current: int, global_sample_indices: list[GlobalSampleIndex]
    ):
        self.msg = f"Error processing samples (current: {current}, global_sample_indices: {global_sample_indices})"
        self.tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        self.__traceback__ = e.__traceback__
        self.current = current
        self.global_sample_indices = global_sample_indices

    def __str__(self):
        return self.msg

    def json(self) -> dict:
        return json.dumps(
            {
                "msg": self.msg,
                "tb": self.tb,
                "current": self.current,
                "global_sample_indices": [
                    i.model_dump() for i in self.global_sample_indices
                ],
            }
        )

    @classmethod
    def from_json(cls, s: bytes) -> "ProcessNextSamplesException":
        json_content = json.loads(s)
        e = cls(
            Exception(),
            json_content["current"],
            [GlobalSampleIndex(**i) for i in json_content["global_sample_indices"]],
        )
        e.msg = json_content["msg"]
        e.tb = json_content["tb"]
        return e

    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=500,
            detail=self.msg + "\n" + self.tb,
            headers={
                "X-Lavender-Data-Error": "SAMPLE_PROCESSING_ERROR",
                "X-Lavender-Data-Sample-Current": str(self.current),
            },
        )


def decollate(batch: dict) -> dict:
    _batch = {}
    for k, v in batch.items():
        if torch is not None and isinstance(v, torch.Tensor):
            try:
                _batch[k] = v.item()
            except RuntimeError:
                _batch[k] = v[0]
        elif isinstance(v, list) and len(v) == 1:
            _batch[k] = v[0]
        elif isinstance(v, dict):
            _batch[k] = decollate(v)
        else:
            _batch[k] = v
    return _batch


class NoSamplesFound(Exception):
    pass


def gather_samples(
    params: CollateSamplesParams, join_method: JoinMethod = "left"
) -> dict:
    reader = get_reader_instance()

    current = params.current
    global_sample_indices = params.global_sample_indices
    samples = params.samples
    collater = params.collater

    if samples is None:
        samples = []
        for i in global_sample_indices:
            try:
                samples.append(reader.get_sample(i, join_method))
            except InnerJoinSampleInsufficient:
                pass

    if len(samples) == 0:
        raise NoSamplesFound()

    batch = (
        CollaterRegistry.get(collater["name"]).collate(samples)
        if collater is not None
        else CollaterRegistry.get("default").collate(samples)
    )

    batch["_lavender_data_indices"] = [i.index for i in global_sample_indices]
    batch["_lavender_data_current"] = current

    return batch


def organize_preprocessors(
    preprocessors: list[IterationPreprocessor],
) -> list[list[tuple[Preprocessor, dict]]]:
    current_preprocessors = [
        (PreprocessorRegistry.get(p["name"]), p["params"]) for p in preprocessors
    ]
    seen: set[str] = set()
    result: list[list[tuple[Preprocessor, dict]]] = []
    while len(current_preprocessors) > 0:
        execute_this_round: list[tuple[Preprocessor, dict]] = []
        _current_preprocessors = []
        for preprocessor, params in current_preprocessors:
            deps = [d for d in preprocessor.depends_on]

            if (
                # it has no dependencies
                len(preprocessor.depends_on) == 0
                # or all dependencies have been executed
                or all(d in seen for d in deps)
            ):
                execute_this_round.append((preprocessor, params))
            else:
                # unprocessable if some dependencies are not met
                for dep in deps:
                    if not dep in [p[0].name for p in current_preprocessors]:
                        raise ValueError(
                            f"Preprocessor '{preprocessor.name}' depends on {deps} but '{dep}' is not included in {[p[0].name for p in current_preprocessors]}."
                        )
                _current_preprocessors.append((preprocessor, params))
        for preprocessor, params in execute_this_round:
            seen.add(preprocessor.name)
        current_preprocessors = _current_preprocessors
        result.append(execute_this_round)
    return result


def _process_next_samples(
    params: ProcessNextSamplesParams,
    join_method: JoinMethod = "left",
) -> dict:
    batch = gather_samples(params, join_method)

    if params.preprocessors is not None:
        preprocessors = organize_preprocessors(params.preprocessors)
        executor = ThreadPoolExecutor()
        for preprocessor_group in preprocessors:
            futures = []
            for preprocessor, args in preprocessor_group:
                futures.append(executor.submit(preprocessor.process, batch, **args))
            for future in as_completed(futures):
                batch.update(future.result())
        executor.shutdown()

    if params.batch_size == 0:
        batch = decollate(batch)

    return batch


@pool_task()
def process_next_samples(
    params: ProcessNextSamplesParams,
    max_retry_count: int,
    join_method: JoinMethod = "left",
) -> dict:
    for i in range(max_retry_count + 1):
        try:
            return _process_next_samples(params, join_method)
        except NoSamplesFound as e:
            raise ProcessNextSamplesException(
                e=e,
                current=params.current,
                global_sample_indices=params.global_sample_indices,
            )
        except Exception as e:
            error = ProcessNextSamplesException(
                e=e,
                current=params.current,
                global_sample_indices=params.global_sample_indices,
            )
            logger = get_logger(__name__)
            if i < max_retry_count:
                logger.warning(f"{str(error)}, retrying... ({i+1}/{max_retry_count})")
            else:
                logger.exception(error)
                raise error
