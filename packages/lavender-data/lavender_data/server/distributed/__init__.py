from typing import Annotated, Optional

from fastapi import Depends, HTTPException

from lavender_data.server.settings import AppSettings
from lavender_data.server.auth import AuthorizationHeader

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


def get_cluster_auth(
    auth: AuthorizationHeader, cluster: CurrentCluster, settings: AppSettings
):
    if settings.lavender_data_disable_auth:
        return None

    salt = auth.username
    hashed = auth.password

    if not cluster.is_valid_auth(salt, hashed):
        raise HTTPException(status_code=401, detail="API key is locked")

    return None


ClusterAuth: None = Depends(get_cluster_auth)
