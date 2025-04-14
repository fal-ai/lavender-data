import random
from typing import Optional

from fastapi import HTTPException, APIRouter, Response, BackgroundTasks

from sqlmodel import select, col
from sqlalchemy.exc import NoResultFound
from pydantic import BaseModel

from lavender_data.server.cache import CacheClient
from lavender_data.server.db import DbSession
from lavender_data.server.db.models import (
    Iteration,
    IterationPublic,
    DatasetPublic,
    DatasetColumnPublic,
    Shardset,
    ShardsetPublic,
    ShardPublic,
    Dataset,
    IterationFilter,
    IterationPreprocessor,
    IterationCollater,
)
from lavender_data.server.services.iterations import (
    IterationState,
    IterationStateException,
    Progress,
    get_next_samples,
    get_iteration_with_same_config,
    process_next_samples,
)
from lavender_data.server.services.registries import (
    PreprocessorRegistry,
    FilterRegistry,
    CollaterRegistry,
)
from lavender_data.server.settings import AppSettings, get_settings
from lavender_data.server.auth import CurrentApiKey
from lavender_data.logging import get_logger

router = APIRouter(
    prefix="/iterations",
    tags=["iterations"],
    dependencies=(
        [CurrentApiKey] if not get_settings().lavender_data_disable_auth else []
    ),
)
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
    rank: Optional[int] = None
    world_size: Optional[int] = None
    wait_participant_threshold: Optional[float] = None


@router.post("/")
def create_iteration(
    params: CreateIterationParams, session: DbSession, cache: CacheClient
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
                    detail="preprocessor must be one of the following: ["
                    + ", ".join(PreprocessorRegistry.list())
                    + "]",
                )

    if params.filters is not None:
        for f in params.filters:
            if f["name"] not in FilterRegistry.list():
                raise HTTPException(
                    status_code=400,
                    detail="filter must be one of the following: ["
                    + ", ".join(FilterRegistry.list())
                    + "]",
                )

    if params.collater is not None:
        if params.collater["name"] not in CollaterRegistry.list():
            raise HTTPException(
                status_code=400,
                detail="collater must be one of the following: ["
                + ", ".join(CollaterRegistry.list())
                + "]",
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
        dataset=dataset,
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

    iteration_with_same_config = None
    iteration_with_same_config_id = get_iteration_with_same_config(iteration, cache)
    if iteration_with_same_config_id is not None:
        try:
            iteration_with_same_config = session.get_one(
                Iteration, iteration_with_same_config_id
            )

            state = IterationState(iteration_with_same_config.id, cache)
            if not state.exists():
                iteration_with_same_config = None

            if params.rank in state.get_ranks():
                # this rank already requested to create an iteration with this config
                # it means "create_iteration" called twice, which happens when
                # the training script is restarted. thus iteration should be initialized again
                iteration_with_same_config = None

            if (params.world_size is not None) and (
                set(state.get_ranks()) == set(range(params.world_size))
            ):
                # all nodes have already joined
                # this means training script is restarted. thus iteration should be initialized again
                iteration_with_same_config = None

        except NoResultFound:
            pass

    if iteration_with_same_config is not None:
        iteration = iteration_with_same_config
    else:
        session.add(iteration)
        session.commit()
        session.refresh(iteration)

    state = IterationState(iteration.id, cache)
    state.init(
        iteration,
        (
            (params.wait_participant_threshold or 10)
            if params.world_size is None
            else None
        ),
    )

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


def process_next_samples_task(
    iteration_id: str,
    indices: list[int],
    samples: list[dict],
    cache_key: str,
    cache_ttl: int,
    cache: CacheClient,
):
    try:
        state = IterationState(iteration_id, cache)
        content = process_next_samples(state, indices, samples)
        cache.set(cache_key, content, ex=cache_ttl)
    except Exception as e:
        logger.exception(f"Error processing next samples for iteration {iteration_id}")
        cache.set(cache_key, f"error:{e}", ex=cache_ttl)


@router.get("/{iteration_id}/next")
def get_next(
    iteration_id: str,
    session: DbSession,
    cache: CacheClient,
    settings: AppSettings,
    background_tasks: BackgroundTasks,
    rank: int = 0,
    async_mode: bool = False,
    no_cache: bool = False,
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

    indices, samples = get_next_samples(state, rank)

    if async_mode:
        cache_key = state.get_batch_cache_key(indices)
        cache_ttl = settings.lavender_data_batch_cache_ttl
        if cache.exists(cache_key) and not no_cache:
            cache.expire(cache_key, cache_ttl)
        else:
            cache.set(cache_key, "pending", ex=cache_ttl)
            background_tasks.add_task(
                process_next_samples_task,
                iteration_id=iteration_id,
                indices=indices,
                samples=samples,
                cache_key=cache_key,
                cache_ttl=cache_ttl,
                cache=cache,
            )
        return Response(content=cache_key, media_type="application/octet-stream")
    else:
        content = process_next_samples(state, indices, samples)
        return Response(content=content, media_type="application/octet-stream")


@router.get("/{iteration_id}/next/{cache_key}")
def get_next_async_result(
    iteration_id: str, cache_key: str, cache: CacheClient
) -> bytes:
    content = cache.get(cache_key)
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")
    if content == b"pending":
        raise HTTPException(status_code=202, detail="Content is still being processed")
    if content.startswith(b"error:"):
        raise HTTPException(status_code=400, detail=content[6:].decode("utf-8"))
    return Response(content=content, media_type="application/octet-stream")


@router.post("/{iteration_id}/complete/{index}")
def complete_index(iteration_id: str, index: str, cache: CacheClient):
    state = IterationState(iteration_id, cache)
    if not state.exists():
        raise HTTPException(
            status_code=404, detail="Iteration not found or not started"
        )
    state.complete(index)
    return


@router.get("/{iteration_id}/progress")
def get_progress(iteration_id: str, session: DbSession, cache: CacheClient) -> Progress:
    state = IterationState(iteration_id, cache)
    if not state.exists():
        raise HTTPException(status_code=404, detail="Iteration not found")
    return state.get_progress()


@router.post("/{iteration_id}/pushback")
def pushback(iteration_id: str, cache: CacheClient):
    state = IterationState(iteration_id, cache)
    if not state.exists():
        raise HTTPException(status_code=404, detail="Iteration not found")
    state.pushback_inprogress()
    return
