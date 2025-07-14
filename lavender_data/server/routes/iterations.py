import random
from typing import Optional

from fastapi import HTTPException, APIRouter, Response, Depends

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
    IterationCategorizer,
    IterationCollater,
    IterationPreprocessor,
    IterationShardsetLink,
)
from lavender_data.serialize import _bytes_to_int
from lavender_data.server.background_worker import (
    CurrentBackgroundWorker,
    CurrentSharedMemory,
)
from lavender_data.server.distributed import CurrentCluster
from lavender_data.server.reader import ReaderInstance
from lavender_data.server.dataset import refine_sample_previewable
from lavender_data.server.iteration import (
    IterationState,
    CurrentIterationState,
    Progress,
    ProcessNextSamplesException,
    process_next_samples,
    process_next_samples_and_store,
    set_cluster_sync,
    get_iteration_hash,
    set_iteration_hash,
    get_iteration_id_from_hash,
    get_iteration_id_from_hash_from_head,
)
from lavender_data.server.registries import (
    FilterRegistry,
    CategorizerRegistry,
    CollaterRegistry,
    PreprocessorRegistry,
)
from lavender_data.server.settings import AppSettings
from lavender_data.server.auth import AppAuth
from lavender_data.server.shardset.span import get_main_shardset

try:
    import torch
except ImportError:
    torch = None

router = APIRouter(
    prefix="/iterations",
    tags=["iterations"],
    dependencies=[Depends(AppAuth(api_key_auth=True, cluster_auth=True))],
)


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
    categorizer: Optional[IterationCategorizer] = None
    collater: Optional[IterationCollater] = None
    preprocessors: Optional[list[IterationPreprocessor]] = None

    shuffle: Optional[bool] = None
    shuffle_seed: Optional[int] = None
    shuffle_block_size: Optional[int] = None

    batch_size: Optional[int] = None

    replication_pg: Optional[list[list[int]]] = None
    rank: Optional[int] = None
    world_size: Optional[int] = None
    wait_participant_threshold: Optional[float] = None

    cluster_sync: Optional[bool] = None


@router.post("/")
def create_iteration(
    params: CreateIterationParams,
    session: DbSession,
    cache: CacheClient,
    cluster: CurrentCluster,
    settings: AppSettings,
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

    if params.filters is not None:
        for f in params.filters:
            if f["name"] not in FilterRegistry.all():
                raise HTTPException(
                    status_code=400,
                    detail="filter must be one of the following: ["
                    + ", ".join(FilterRegistry.all())
                    + "]",
                )

    if params.categorizer is not None:
        if params.categorizer["name"] not in CategorizerRegistry.all():
            raise HTTPException(
                status_code=400,
                detail="categorizer must be one of the following: ["
                + ", ".join(CategorizerRegistry.all())
                + "]",
            )

    if params.collater is not None:
        if params.collater["name"] not in CollaterRegistry.all():
            raise HTTPException(
                status_code=400,
                detail="collater must be one of the following: ["
                + ", ".join(CollaterRegistry.all())
                + "]",
            )

    if params.preprocessors is not None:
        for preprocessor in params.preprocessors:
            if preprocessor["name"] not in PreprocessorRegistry.all():
                raise HTTPException(
                    status_code=400,
                    detail="preprocessor must be one of the following: ["
                    + ", ".join(PreprocessorRegistry.all())
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

    total_samples = get_main_shardset(shardsets).total_samples

    cluster_sync = (
        params.cluster_sync
        if params.cluster_sync is not None
        else settings.lavender_data_cluster_enabled
    )

    iteration = Iteration(
        dataset_id=dataset.id,
        total=total_samples,
        filters=params.filters,
        categorizer=params.categorizer,
        collater=params.collater,
        preprocessors=params.preprocessors,
        shuffle=shuffle,
        shuffle_seed=params.shuffle_seed,
        shuffle_block_size=params.shuffle_block_size,
        batch_size=batch_size,
        shardsets=shardsets,
        replication_pg=params.replication_pg,
    )
    iteration_hash = get_iteration_hash(iteration, params.dataset_id)
    iteration_with_same_config = None

    with cache.lock(f"iteration_create_{iteration_hash}"):
        iteration_with_same_config_id = get_iteration_id_from_hash(
            iteration_hash, cache
        )

        if cluster and cluster_sync and not cluster.is_head:
            iteration_with_same_config_id = get_iteration_id_from_hash_from_head(
                iteration_hash, cluster
            )

        if iteration_with_same_config_id is not None:
            try:
                iteration_with_same_config = session.get_one(
                    Iteration, iteration_with_same_config_id
                )

                state = IterationState(iteration_with_same_config.id, cache)
                if state.exists():
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

        if cluster:
            iteration_shardset_links = [
                IterationShardsetLink(
                    iteration_id=iteration.id, shardset_id=shardset.id
                )
                for shardset in iteration.shardsets
            ]
            cluster.sync_changes([iteration, *iteration_shardset_links])
            if cluster_sync:
                set_cluster_sync(iteration.id, cache, cluster)

        set_iteration_hash(
            iteration.id,
            iteration_hash=iteration_hash,
            ttl=(params.wait_participant_threshold or 10),
            cache=cache,
        )
    state = IterationState(iteration.id, cache)
    state.init(iteration)

    return iteration


@router.get("/iteration-id-from-hash")
def cluster_get_iteration_id_from_hash(
    iteration_hash: str, cache: CacheClient, cluster: CurrentCluster
) -> str:
    if cluster is None:
        raise HTTPException(status_code=400, detail="Cluster not found")
    if not cluster.is_head:
        raise HTTPException(
            status_code=400, detail="Worker node cannot get iteration id from hash"
        )
    return get_iteration_id_from_hash(iteration_hash, cache)


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


@router.get("/{iteration_id}/next-preview")
def get_next_preview(
    iteration_id: str,
    state: CurrentIterationState,
    reader: ReaderInstance,
) -> dict:
    _, params = state.get_next_samples(0)

    try:
        batch = process_next_samples(params, 0)
    except ProcessNextSamplesException as e:
        raise e.to_http_exception()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # TODO decollate
    sample = batch
    sample = refine_sample_previewable(sample)

    return sample


@router.get("/{iteration_id}/next")
def get_next(
    iteration_id: str,
    shared_memory: CurrentSharedMemory,
    settings: AppSettings,
    state: CurrentIterationState,
    rank: int = 0,
    no_cache: bool = False,
    max_retry_count: int = 0,
) -> bytes:
    if max_retry_count < 0:
        raise HTTPException(status_code=400, detail="max_retry_count must be >= 0")

    cache_key, params = state.get_next_samples(rank)

    """
    TODO if cluster_mode is true
    fetch ProcessNextSamplesParams from head node
    all operations related to iteration_state should be done in head node
    """

    cache_ttl = settings.lavender_data_batch_cache_ttl

    if no_cache:
        shared_memory.delete(cache_key)

    if shared_memory.exists(cache_key):
        shared_memory.expire(cache_key, cache_ttl)
    else:
        process_next_samples_and_store(
            params=params,
            max_retry_count=max_retry_count,
            cache_key=cache_key,
            cache_ttl=cache_ttl,
            shared_memory=shared_memory,
        )

    content = shared_memory.get(cache_key)
    if content.startswith(b"processing_error:"):
        e = ProcessNextSamplesException.from_json(content[17:])
        raise e.to_http_exception()
    if content.startswith(b"error:"):
        raise HTTPException(status_code=500, detail=content[6:].decode("utf-8"))

    content = content[4:]

    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={
            "X-Lavender-Data-Sample-Current": str(params.current),
        },
    )


class SubmitNextResponse(BaseModel):
    cache_key: str


@router.post("/{iteration_id}/next")
def submit_next(
    iteration_id: str,
    settings: AppSettings,
    background_worker: CurrentBackgroundWorker,
    shared_memory: CurrentSharedMemory,
    state: CurrentIterationState,
    rank: int = 0,
    no_cache: bool = False,
    max_retry_count: int = 0,
) -> SubmitNextResponse:
    if max_retry_count < 0:
        raise HTTPException(status_code=400, detail="max_retry_count must be >= 0")

    cache_key, params = state.get_next_samples(rank)
    cache_ttl = settings.lavender_data_batch_cache_ttl

    if no_cache:
        shared_memory.delete(cache_key)

    if shared_memory.exists(cache_key):
        shared_memory.expire(cache_key, cache_ttl)
    else:
        background_worker.process_pool_submit(
            process_next_samples_and_store,
            params=params,
            max_retry_count=max_retry_count,
            cache_key=cache_key,
            cache_ttl=cache_ttl,
            shared_memory=shared_memory,
        )

    return SubmitNextResponse(cache_key=cache_key)


@router.get("/{iteration_id}/next/{cache_key}")
def get_submitted_result(
    iteration_id: str,
    cache_key: str,
    shared_memory: CurrentSharedMemory,
) -> bytes:
    content = shared_memory.get(cache_key)
    if content is None:
        raise HTTPException(status_code=202, detail="Data is still being processed")
    if content.startswith(b"processing_error:"):
        e = ProcessNextSamplesException.from_json(content[17:])
        raise e.to_http_exception()
    if content.startswith(b"error:"):
        raise HTTPException(status_code=500, detail=content[6:].decode("utf-8"))

    current = _bytes_to_int(content[:4])
    content = content[4:]

    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={
            "X-Lavender-Data-Sample-Current": str(current),
        },
    )


@router.post("/{iteration_id}/complete/{index}")
def complete_index(iteration_id: str, index: int, state: CurrentIterationState):
    return state.complete(index)


@router.get("/{iteration_id}/progress")
def get_progress(iteration_id: str, state: CurrentIterationState) -> Progress:
    return state.get_progress()


@router.post("/{iteration_id}/pushback")
def pushback(iteration_id: str, state: CurrentIterationState):
    return state.pushback_inprogress()


@router.post("/{iteration_id}/state/set-cluster-sync")
def cluster_set_cluster_sync(
    iteration_id: str, cache: CacheClient, cluster: CurrentCluster
):
    if cluster is None:
        raise HTTPException(status_code=400, detail="Cluster not found")
    if cluster.is_head:
        raise HTTPException(status_code=400, detail="Head node cannot set cluster sync")
    return set_cluster_sync(iteration_id, cache, cluster)


@router.post("/{iteration_id}/state/{operation}")
def cluster_operation(
    iteration_id: str,
    operation: str,
    state: CurrentIterationState,
    cluster: CurrentCluster,
    params: dict,
):
    if cluster is None:
        raise HTTPException(status_code=400, detail="Cluster not found")
    if not cluster.is_head:
        raise HTTPException(
            status_code=400, detail="Worker node cannot perform state operations"
        )

    if operation == "exists":
        return state.exists()
    elif operation == "pushback_inprogress":
        return state.pushback_inprogress()
    elif operation == "complete":
        return state.complete(params["index"])
    elif operation == "filtered":
        return state.filtered(params["index"])
    elif operation == "failed":
        return state.failed(params["index"])
    elif operation == "next_item":
        return state.next_item(params["rank"])
    elif operation == "get_ranks":
        return state.get_ranks()
    elif operation == "get_progress":
        return state.get_progress()
    elif operation == "get_next_samples":
        return state.get_next_samples(params["rank"])
    else:
        raise HTTPException(status_code=400, detail="Invalid operation")
