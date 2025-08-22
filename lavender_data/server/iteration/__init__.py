from typing import Annotated

from fastapi import HTTPException, Depends

from lavender_data.server.cache import CacheClient
from lavender_data.server.distributed import CurrentCluster

from .process import (
    ProcessNextSamplesParams,
    ProcessNextSamplesException,
    process_next_samples,
)
from .hash import (
    get_iteration_hash,
    set_iteration_hash,
    get_iteration_id_from_hash,
)
from .iteration_state import (
    Progress,
    InProgressIndex,
    IterationStateException,
    IterationStateOps,
    IterationState,
    IterationStateClusterOps,
)
from .prefetcher import (
    IterationPrefetcherPool,
    IterationPrefetcher,
    NotFetchedYet,
)

__all__ = [
    "ProcessNextSamplesParams",
    "ProcessNextSamplesException",
    "process_next_samples",
    "get_iteration_hash",
    "set_iteration_hash",
    "get_iteration_id_from_hash",
    "Progress",
    "InProgressIndex",
    "IterationStateException",
    "IterationStateOps",
    "IterationState",
    "IterationStateClusterOps",
    "get_iteration_state",
    "CurrentIterationState",
    "CurrentIterationPrefetcher",
    "CurrentIterationPrefetcherPool",
    "setup_iteration_prefetcher_pool",
    "shutdown_iteration_prefetcher_pool",
    "NotFetchedYet",
]


def get_iteration_state(
    iteration_id: str, cache: CacheClient, cluster: CurrentCluster
) -> IterationStateOps:
    state = None

    if cluster is not None and not cluster.is_head:
        state = IterationStateClusterOps(iteration_id, cluster)

    if state is None:
        state = IterationState(iteration_id, cache)

    if not state.exists():
        raise HTTPException(status_code=404, detail="Iteration not initialized")

    return state


CurrentIterationState = Annotated[IterationStateOps, Depends(get_iteration_state)]


iteration_prefetcher_pool = None


def setup_iteration_prefetcher_pool():
    global iteration_prefetcher_pool
    iteration_prefetcher_pool = IterationPrefetcherPool()


def shutdown_iteration_prefetcher_pool():
    global iteration_prefetcher_pool
    iteration_prefetcher_pool.shutdown()


def get_iteration_prefetcher_pool():
    global iteration_prefetcher_pool
    if iteration_prefetcher_pool is None:
        raise Exception("Iteration prefetcher pool not initialized")
    return iteration_prefetcher_pool


CurrentIterationPrefetcherPool = Annotated[
    IterationPrefetcherPool, Depends(get_iteration_prefetcher_pool)
]


def get_iteration_prefetcher(iteration_id: str) -> IterationPrefetcher:
    global iteration_prefetcher_pool
    if iteration_prefetcher_pool is None:
        raise Exception("Iteration prefetcher pool not initialized")
    try:
        return iteration_prefetcher_pool.get_prefetcher(iteration_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Iteration prefetcher not found")


CurrentIterationPrefetcher = Annotated[
    IterationPrefetcher, Depends(get_iteration_prefetcher)
]
