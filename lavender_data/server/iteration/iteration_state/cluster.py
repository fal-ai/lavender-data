import time
from typing import Optional

from lavender_data.server.cache import CacheClient
from lavender_data.server.distributed import CurrentCluster
from lavender_data.server.reader import (
    GlobalSampleIndex,
)

from lavender_data.server.iteration import ProcessNextSamplesParams

from .abc import IterationStateOps, Progress, IterationStateException


class IterationStateClusterOps(IterationStateOps):
    def __init__(self, iteration_id: str, cluster: CurrentCluster):
        self.iteration_id = iteration_id
        self.cluster = cluster

    def _head(self, path: str, json: dict) -> dict:
        try:
            return self.cluster.head_post(
                f"/iterations/{self.iteration_id}/state/{path}", json
            )
        except Exception as e:
            raise IterationStateException(str(e))

    def exists(self) -> bool:
        return self._head("exists", {})

    def pushback_inprogress(self) -> None:
        return self._head("pushback_inprogress", {})

    def complete(self, index: int) -> None:
        return self._head("complete", {"index": index})

    def filtered(self, index: int) -> None:
        return self._head("filtered", {"index": index})

    def failed(self, index: int) -> None:
        return self._head("failed", {"index": index})

    def next_item(self, rank: int) -> GlobalSampleIndex:
        return GlobalSampleIndex(**self._head("next_item", {"rank": rank}))

    def get_ranks(self) -> list[int]:
        return self._head("get_ranks", {})

    def get_progress(self) -> Progress:
        return Progress(**self._head("get_progress", {}))

    def get_next_samples(self, rank: int) -> tuple[str, ProcessNextSamplesParams]:
        cache_key, params = self._head("get_next_samples", {"rank": rank})
        return cache_key, ProcessNextSamplesParams(**params)


def set_cluster_sync(
    iteration_id: str,
    cache: CacheClient,
    cluster: CurrentCluster,
):
    cache.set(f"cluster_sync:{iteration_id}", "true")
    if cluster is not None and cluster.is_head:
        try:
            cluster.broadcast_post(
                f"/iterations/{iteration_id}/state/set-cluster-sync", {}
            )
        except Exception as e:
            raise IterationStateException(str(e))


def is_cluster_sync(
    iteration_id: str,
    cache: CacheClient,
) -> bool:
    return cache.get(f"cluster_sync:{iteration_id}") == b"true"


def get_iteration_id_from_hash_from_head(
    iteration_hash: str, cluster: CurrentCluster, timeout: int = 10
) -> Optional[str]:
    start = time.time()
    while True:
        try:
            iteration_id = cluster.head_get(
                f"/iterations/iteration-id-from-hash?iteration_hash={iteration_hash}",
            )
            if iteration_id is None:
                raise IterationStateException("Iteration not found")
            return iteration_id
        except Exception as e:
            if time.time() - start > timeout:
                raise IterationStateException(str(e))
            time.sleep(0.1)
