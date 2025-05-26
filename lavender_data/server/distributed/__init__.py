from typing import Annotated, Optional

from fastapi import Depends

from lavender_data.logging import get_logger

from .cluster import Cluster

cluster = None


def setup_cluster(
    enabled: bool,
    head_url: str,
    node_url: str,
    secret: str,
    disable_auth: bool = False,
) -> Cluster:
    if not enabled:
        return None

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
        try:
            cluster.deregister()
        except Exception as e:
            get_logger(__name__).warning(f"Failed to deregister: {e}")


def get_cluster() -> Optional[Cluster]:
    global cluster
    return cluster


CurrentCluster = Annotated[Optional[Cluster], Depends(get_cluster)]
