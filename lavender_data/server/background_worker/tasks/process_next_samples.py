from lavender_data.server.iteration.process_next_samples import (
    ProcessNextSamplesParams,
    ProcessNextSamplesException,
    process_next_samples,
)
from lavender_data.logging import get_logger

from lavender_data.server.background_worker.memory import Memory


def process_next_samples_task(
    params: ProcessNextSamplesParams,
    max_retry_count: int,
    cache_key: str,
    cache_ttl: int,
    *,
    memory: Memory,
):
    logger = get_logger(__name__)
    try:
        content = process_next_samples(params, max_retry_count)
        memory.set(cache_key, content, ex=cache_ttl)
    except ProcessNextSamplesException as e:
        logger.error(e)
        memory.set(cache_key, f"processing_error:{e.json()}", ex=cache_ttl)
    except Exception as e:
        logger.exception(e)
        memory.set(cache_key, f"error:{e}", ex=cache_ttl)
