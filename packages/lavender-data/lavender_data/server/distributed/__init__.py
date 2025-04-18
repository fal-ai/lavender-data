from typing import Annotated, Optional

from fastapi import Depends

from .cluster import Cluster

cluster = None


def setup_cluster(
    head_url: str,
    node_url: str,
    secret: str,
    disable_auth: bool = False,
) -> Cluster:
    global cluster
    if secret == "" and not disable_auth:
        raise ValueError("LAVENDER_DATA_CLUSTER_SECRET is not set")
    cluster = Cluster(head_url, node_url, secret, disable_auth)
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
