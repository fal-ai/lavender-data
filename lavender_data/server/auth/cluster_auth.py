from fastapi import Depends, HTTPException

from lavender_data.server.settings import AppSettings
from lavender_data.server.auth.header import AuthorizationHeader

from lavender_data.server.distributed import CurrentCluster


def cluster_auth(
    auth: AuthorizationHeader, cluster: CurrentCluster, settings: AppSettings
):
    if settings.lavender_data_disable_auth:
        return None

    if not settings.lavender_data_cluster_enabled or cluster is None:
        raise HTTPException(status_code=401, detail="Cluster not enabled")

    salt = auth.username
    hashed = auth.password

    if not cluster.is_valid_auth(salt, hashed):
        raise HTTPException(status_code=401, detail="Invalid cluster auth")

    return None


ClusterAuth: None = Depends(cluster_auth)
