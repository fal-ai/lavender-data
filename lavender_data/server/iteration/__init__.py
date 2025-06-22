from typing import Annotated

from fastapi import HTTPException, Depends

from lavender_data.server.cache import CacheClient
from lavender_data.server.distributed import CurrentCluster

from .process import (
    ProcessNextSamplesParams,
    ProcessNextSamplesException,
    process_next_samples,
    process_next_samples_and_store,
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
    is_cluster_sync,
    set_cluster_sync,
    get_iteration_id_from_hash_from_head,
)

__all__ = [
    "ProcessNextSamplesParams",
    "ProcessNextSamplesException",
    "process_next_samples",
    "process_next_samples_and_store",
    "get_iteration_hash",
    "set_iteration_hash",
    "get_iteration_id_from_hash",
    "get_iteration_id_from_hash_from_head",
    "Progress",
    "InProgressIndex",
    "IterationStateException",
    "IterationStateOps",
    "IterationState",
    "IterationStateClusterOps",
    "is_cluster_sync",
    "set_cluster_sync",
    "get_iteration_state",
    "CurrentIterationState",
]


def get_iteration_state(
    iteration_id: str, cache: CacheClient, cluster: CurrentCluster
) -> IterationState:
    state = None

    if is_cluster_sync(iteration_id, cache):
        if cluster is None:
            raise HTTPException(status_code=400, detail="Cluster not found")
        if not cluster.is_head:
            state = IterationStateClusterOps(iteration_id, cluster)

    if state is None:
        state = IterationState(iteration_id, cache)

    if not state.exists():
        raise HTTPException(status_code=404, detail="Iteration not initialized")

    return state


CurrentIterationState = Annotated[IterationStateOps, Depends(get_iteration_state)]
