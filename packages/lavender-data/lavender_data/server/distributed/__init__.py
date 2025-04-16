from typing import Annotated, Optional

from fastapi import Depends

from .cluster import Cluster

cluster = None


def setup_cluster(
    is_head: bool,
    head_url: str,
    node_url: str,
) -> Cluster:
    global cluster
    cluster = Cluster(is_head, head_url, node_url)
    return cluster


def cleanup_cluster():
    global cluster
    if cluster is None:
        return

    if not cluster.is_head:
        cluster.deregister()


def get_cluster() -> Optional[Cluster]:
    global cluster
    return cluster


CurrentCluster = Annotated[Optional[Cluster], Depends(get_cluster)]
