import random
from typing import Optional

from fastapi import HTTPException, APIRouter, Response

from sqlmodel import select, col
from sqlalchemy.exc import NoResultFound
from pydantic import BaseModel

from lavender_data.server.cache import RedisClient
from lavender_data.server.db import DbSession
from lavender_data.server.db.models import (
    Iteration,
    IterationPublic,
    DatasetPublic,
    DatasetColumn,
    DatasetColumnPublic,
    Shardset,
    ShardsetPublic,
    ShardPublic,
    Dataset,
    IterationFilter,
    IterationPreprocessor,
    IterationCollater,
)
from lavender_data.server.reader import ReaderInstance
from lavender_data.server.services.iterations import (
    IterationState,
    IterationStateException,
    Progress,
)
from lavender_data.server.services.registries import (
    PreprocessorRegistry,
    FilterRegistry,
    CollaterRegistry,
)
from lavender_data.serialize import serialize_sample
from lavender_data.logging import get_logger

try:
    import torch
except ImportError:
    torch = None


router = APIRouter(prefix="/iterations", tags=["iterations"])
logger = get_logger(__name__)


@router.get("/")
def get_iterations(
    session: DbSession,
    dataset_id: Optional[str] = None,
) -> list[IterationPublic]:
    query = select(Iteration)
    if dataset_id is not None:
        query = query.where(Iteration.dataset_id == dataset_id)
    query = query.order_by(Iteration.created_at.desc())
    return session.exec(query).all()


class CreateIterationParams(BaseModel):
    dataset_id: str
    shardsets: Optional[list[str]] = None

    filters: Optional[list[IterationFilter]] = None
    preprocessors: Optional[list[IterationPreprocessor]] = None
    collater: Optional[IterationCollater] = None

    shuffle: Optional[bool] = None
    shuffle_seed: Optional[int] = None
    shuffle_block_size: Optional[int] = None

    batch_size: Optional[int] = None

    replication_pg: Optional[list[list[int]]] = None


@router.post("/")
def create_iteration(
    params: CreateIterationParams, session: DbSession, cache: RedisClient
) -> IterationPublic:
    shuffle = params.shuffle or False
    batch_size = params.batch_size or 0

    if shuffle:
        if params.shuffle_seed is None:
            params.shuffle_seed = random.randint(0, 1000000)
        if params.shuffle_block_size is None:
            raise HTTPException(
                status_code=400,
                detail="shuffle_block_size is required if shuffle is true",
            )
        if params.shuffle_block_size < 1:
            raise HTTPException(
                status_code=400,
                detail="shuffle_block_size must be a positive integer",
            )
    else:
        params.shuffle_seed = None
        params.shuffle_block_size = None

    if batch_size < 0:
        raise HTTPException(status_code=400, detail="batch_size must be >= 0")

    if params.preprocessors is not None:
        for preprocessor in params.preprocessors:
            if preprocessor["name"] not in PreprocessorRegistry.list():
                raise HTTPException(
                    status_code=400,
                    detail="preprocessor must be one of the following: "
                    + ", ".join(PreprocessorRegistry.list()),
                )

    if params.filters is not None:
        for f in params.filters:
            if f["name"] not in FilterRegistry.list():
                raise HTTPException(
                    status_code=400,
                    detail="filter must be one of the following: "
                    + ", ".join(FilterRegistry.list()),
                )

    if params.collater is not None:
        if params.collater["name"] not in CollaterRegistry.list():
            raise HTTPException(
                status_code=400,
                detail="collater must be one of the following: "
                + ", ".join(CollaterRegistry.list()),
            )

    try:
        dataset = session.get_one(Dataset, params.dataset_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Dataset not found")

    shardsets_query = select(Shardset).where(Shardset.dataset_id == params.dataset_id)
    if params.shardsets is not None and len(params.shardsets) > 0:
        shardsets_query = shardsets_query.where(col(Shardset.id).in_(params.shardsets))
    shardsets = session.exec(shardsets_query).all()

    if len(shardsets) == 0:
        if params.shardsets is not None and len(params.shardsets) > 0:
            raise HTTPException(
                status_code=400,
                detail="No shardsets found for the provided shardset ids: "
                + ", ".join(params.shardsets),
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="No shardsets found for the dataset. Please create a shardset first.",
            )

    total_samples = shardsets[0].total_samples
    for shardset in shardsets:
        total_samples = min(total_samples, shardset.total_samples)

    iteration = Iteration(
        dataset_id=dataset.id,
        total=total_samples,
        filters=params.filters,
        preprocessors=params.preprocessors,
        collater=params.collater,
        shuffle=shuffle,
        shuffle_seed=params.shuffle_seed,
        shuffle_block_size=params.shuffle_block_size,
        batch_size=batch_size,
        shardsets=shardsets,
        replication_pg=params.replication_pg,
    )
    session.add(iteration)
    session.commit()
    session.refresh(iteration)

    IterationState(iteration.id, cache).init(iteration)

    return iteration


class ShardsetWithShards(ShardsetPublic):
    shards: list[ShardPublic]
    columns: list[DatasetColumnPublic]


class GetIterationResponse(IterationPublic):
    dataset: DatasetPublic
    shardsets: list[ShardsetWithShards]


@router.get("/{iteration_id}")
def get_iteration(iteration_id: str, session: DbSession) -> GetIterationResponse:
    try:
        iteration = session.get_one(Iteration, iteration_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Iteration not found")
    return iteration


@router.get("/{iteration_id}/next")
def get_next(
    iteration_id: str,
    session: DbSession,
    cache: RedisClient,
    reader: ReaderInstance,
    rank: int = 0,
) -> bytes:
    state = IterationState(iteration_id, cache)
    if not state.exists():
        try:
            iteration = session.get_one(Iteration, iteration_id)
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Iteration not found")

        try:
            state.init(iteration)
        except IterationStateException as e:
            raise HTTPException(status_code=400, detail=str(e))

    batch_size = state.get_batch_size()
    iteration_filters = state.get_filters()
    filters = (
        [FilterRegistry.get(**f) for f in iteration_filters]
        if iteration_filters is not None
        else []
    )
    iteration_preprocessors = state.get_preprocessors()
    preprocessors = (
        [PreprocessorRegistry.get(**p) for p in iteration_preprocessors]
        if iteration_preprocessors is not None
        else []
    )
    iteration_collater = state.get_collater()
    collater = (
        CollaterRegistry.get(**iteration_collater)
        if iteration_collater is not None
        else CollaterRegistry.get("default")
    )

    indices = []
    samples = []
    while len(samples) < max(batch_size, 1):
        try:
            current, next_item = state.next_item(rank)
        except IterationStateException as e:
            raise HTTPException(status_code=400, detail=str(e))

        try:
            sample = reader.get_sample(next_item)
        except Exception as e:
            # TODO fault tolerance
            state.failed(next_item.index)
            msg = f"Failed to read sample {next_item.index} (sample {next_item.main_shard.sample_index} of shard {next_item.main_shard.index}): {e.__class__.__name__}({str(e)})"
            logger.exception(msg)
            raise HTTPException(status_code=400, detail=msg)

        filtered = False
        for should_include in filters:
            if not should_include(sample):
                filtered = True
                break
        if filtered:
            state.filtered(next_item.index)
            continue

        samples.append(sample)
        indices.append(next_item.index)

    try:
        batch = collater(samples)
    except Exception as e:
        logger.exception(f'Error in collater: {e.__class__.__name__}("{str(e)}")')
        raise HTTPException(
            status_code=400,
            detail=f'Error in collater: {e.__class__.__name__}("{str(e)}")',
        )

    try:
        for preprocessor in preprocessors:
            batch = preprocessor(batch)
    except Exception as e:
        logger.exception(f'Error in preprocessor: {e.__class__.__name__}("{str(e)}")')
        raise HTTPException(
            status_code=400,
            detail=f'Error in preprocessor: {e.__class__.__name__}("{str(e)}")',
        )

    if batch_size == 0:
        _batch = {}
        for k, v in batch.items():
            if torch is not None and isinstance(v, torch.Tensor):
                _batch[k] = v.item()
            else:
                _batch[k] = v[0]
        batch = _batch

    batch["_lavender_data_indices"] = indices
    batch["_lavender_data_current"] = current

    content = serialize_sample(batch)

    return Response(content=content, media_type="application/octet-stream")


@router.post("/{iteration_id}/complete/{index}")
def complete_index(iteration_id: str, index: str, cache: RedisClient):
    state = IterationState(iteration_id, cache)
    if not state.exists():
        raise HTTPException(
            status_code=404, detail="Iteration not found or not started"
        )
    state.complete(index)
    return


@router.get("/{iteration_id}/progress")
def get_progress(iteration_id: str, session: DbSession, cache: RedisClient) -> Progress:
    state = IterationState(iteration_id, cache)
    if not state.exists():
        raise HTTPException(status_code=404, detail="Iteration not found")
    return state.get_progress()


@router.post("/{iteration_id}/pushback")
def pushback(iteration_id: str, cache: RedisClient):
    state = IterationState(iteration_id, cache)
    if not state.exists():
        raise HTTPException(status_code=404, detail="Iteration not found")
    state.pushback_inprogress()
    return
