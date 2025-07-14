import ujson as json
from typing import Optional
import traceback
import time

from fastapi import HTTPException
from pydantic import BaseModel

try:
    import torch
except ImportError:
    torch = None

from lavender_data.logging import get_logger
from lavender_data.serialize import serialize_sample, _int_to_bytes
from lavender_data.server.background_worker import SharedMemory, pool_task
from lavender_data.server.db.models import (
    IterationPreprocessor,
    IterationCollater,
)
from lavender_data.server.reader import (
    get_reader_instance,
    GlobalSampleIndex,
)
from lavender_data.server.registries import (
    PreprocessorRegistry,
    CollaterRegistry,
)


class ProcessNextSamplesParams(BaseModel):
    current: int
    global_sample_indices: list[GlobalSampleIndex]
    samples: Optional[list[dict]] = None
    collater: Optional[IterationCollater] = None
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


def _decollate(batch: dict) -> dict:
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
            _batch[k] = _decollate(v)
        else:
            _batch[k] = v
    return _batch


def _process_next_samples(params: ProcessNextSamplesParams) -> dict:
    reader = get_reader_instance()

    current = params.current
    global_sample_indices = params.global_sample_indices
    samples = params.samples
    collater = params.collater
    preprocessors = params.preprocessors
    batch_size = params.batch_size

    if samples is None:
        samples = [reader.get_sample(i, join="left") for i in global_sample_indices]

    batch = (
        CollaterRegistry.get(collater["name"]).collate(samples)
        if collater is not None
        else CollaterRegistry.get("default").collate(samples)
    )

    if preprocessors is not None:
        # TODO configurable max_workers
        batch = PreprocessorRegistry.process(
            [(p["name"], p["params"]) for p in preprocessors],
            batch,
        )

    if batch_size == 0:
        batch = _decollate(batch)

    batch["_lavender_data_indices"] = [i.index for i in global_sample_indices]
    batch["_lavender_data_current"] = current

    return batch


@pool_task()
def process_next_samples(
    params: ProcessNextSamplesParams,
    max_retry_count: int,
) -> dict:
    logger = get_logger(__name__)

    for i in range(max_retry_count + 1):
        try:
            return _process_next_samples(params)
        except Exception as e:
            error = ProcessNextSamplesException(
                e=e,
                current=params.current,
                global_sample_indices=params.global_sample_indices,
            )
            if i < max_retry_count:
                logger.warning(f"{str(error)}, retrying... ({i+1}/{max_retry_count})")
            else:
                logger.exception(error)
                raise error


def _format_number(number: int):
    if number < 1000:
        return f"{number} "
    elif number < 1000**2:
        return f"{number/1000:.2f} K"
    elif number < 1000**3:
        return f"{number/1000**2:.2f} M"
    else:
        return f"{number/1000**3:.2f} G"


def _ms(seconds: float):
    return f"{seconds*1000:.2f} ms"


@pool_task()
def process_next_samples_and_store(
    params: ProcessNextSamplesParams,
    max_retry_count: int,
    cache_key: str,
    cache_ttl: int,
    *,
    shared_memory: SharedMemory,
):
    logger = get_logger(__name__)
    try:
        _start = time.perf_counter()
        batch = process_next_samples(params, max_retry_count)
        _process_time = time.perf_counter()
        content = serialize_sample(batch)
        _serialize_time = time.perf_counter()
        shared_memory.set(
            cache_key, _int_to_bytes(params.current) + content, ex=cache_ttl
        )
        _store_time = time.perf_counter()
        logger.debug(
            f"Done processing {cache_key} in {_ms(_store_time - _start)}, "
            f"process: {_ms(_process_time - _start)}, "
            f"serialize: {_ms(_serialize_time - _process_time)}, "
            f"store: {_ms(_store_time - _serialize_time)}, "
            f"size: {_format_number(len(content))}B"
        )
    except ProcessNextSamplesException as e:
        shared_memory.set(cache_key, f"processing_error:{e.json()}", ex=cache_ttl)
    except Exception as e:
        shared_memory.set(cache_key, f"error:{e}", ex=cache_ttl)
