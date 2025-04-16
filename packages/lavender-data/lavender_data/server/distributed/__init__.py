from typing import Annotated, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasicCredentials, HTTPBasic

from .cluster import Cluster

cluster = None


def setup_cluster(
    is_head: bool,
    head_url: str,
    node_url: str,
    secret: str,
    disable_auth: bool = False,
) -> Cluster:
    global cluster
    if secret == "" and not disable_auth:
        raise ValueError("LAVENDER_DATA_CLUSTER_SECRET is not set")
    cluster = Cluster(is_head, head_url, node_url, secret)
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

http_basic = HTTPBasic()
AuthorizationHeader = Annotated[HTTPBasicCredentials, Depends(http_basic)]


def validate_token(auth: AuthorizationHeader, cluster: CurrentCluster):
    salt = auth.username
    hashed = auth.password

    if not cluster.is_valid_auth(salt, hashed):
        raise HTTPException(status_code=401, detail="API key is locked")

    return cluster


ClusterAuth: Cluster = Depends(validate_token)
