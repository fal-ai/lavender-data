import ujson as json
from typing import Optional
import traceback

from fastapi import HTTPException
from pydantic import BaseModel

try:
    import torch
except ImportError:
    torch = None

from lavender_data.logging import get_logger
from lavender_data.serialize import serialize_sample
from lavender_data.server.background_worker.memory import Memory
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
    current: int
    global_sample_indices: list[GlobalSampleIndex]

    def __init__(
        self, msg: str, current: int, global_sample_indices: list[GlobalSampleIndex]
    ):
        self.msg = msg
        self.current = current
        self.global_sample_indices = global_sample_indices

    def json(self) -> dict:
        return json.dumps(
            {
                "msg": self.msg,
                "current": self.current,
                "global_sample_indices": [
                    i.model_dump() for i in self.global_sample_indices
                ],
            }
        )

    @classmethod
    def from_json(cls, s: bytes) -> "ProcessNextSamplesException":
        json_content = json.loads(s)
        return cls(
            json_content["msg"],
            json_content["current"],
            [GlobalSampleIndex(**i) for i in json_content["global_sample_indices"]],
        )

    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=500,
            detail=self.msg,
            headers={
                "X-Lavender-Data-Error": "SAMPLE_PROCESSING_ERROR",
                "X-Lavender-Data-Sample-Current": str(self.current),
            },
        )


def _process_next_samples(params: ProcessNextSamplesParams) -> dict:
    reader = get_reader_instance()

    current = params.current
    global_sample_indices = params.global_sample_indices
    samples = params.samples
    collater = params.collater
    preprocessors = params.preprocessors
    batch_size = params.batch_size

    if samples is None:
        samples = [reader.get_sample(i) for i in global_sample_indices]

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
        _batch = {}
        for k, v in batch.items():
            if torch is not None and isinstance(v, torch.Tensor):
                _batch[k] = v.item()
            else:
                _batch[k] = v[0]
        batch = _batch

    batch["_lavender_data_indices"] = [i.index for i in global_sample_indices]
    batch["_lavender_data_current"] = current

    return batch


def process_next_samples(
    params: ProcessNextSamplesParams,
    max_retry_count: int,
) -> dict:
    logger = get_logger(__name__)

    for i in range(max_retry_count + 1):
        try:
            return _process_next_samples(params)
        except Exception as e:
            tb = traceback.format_exc()
            msg = f"Error processing samples (current: {params.current}, global_sample_indices: {params.global_sample_indices}): {str(e)}\n{tb}"
            if i < max_retry_count:
                logger.warning(f"{msg}, retrying... ({i+1}/{max_retry_count})")
            else:
                logger.error(msg)
                raise ProcessNextSamplesException(
                    msg=msg,
                    current=params.current,
                    global_sample_indices=params.global_sample_indices,
                )


def process_next_samples_task(
    params: ProcessNextSamplesParams,
    max_retry_count: int,
    cache_key: str,
    cache_ttl: int,
    *,
    memory: Memory,
    task_uid: str,
):
    try:
        batch = process_next_samples(params, max_retry_count)
        content = serialize_sample(batch)
        memory.set(cache_key, content, ex=cache_ttl)
    except ProcessNextSamplesException as e:
        memory.set(cache_key, f"processing_error:{e.json()}", ex=cache_ttl)
    except Exception as e:
        memory.set(cache_key, f"error:{e}", ex=cache_ttl)
