from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlmodel import select

from lavender_data.server.distributed import CurrentCluster
from lavender_data.server.distributed.cluster import NodeStatus
from lavender_data.server.auth import AppAuth
from lavender_data.server.db import DbSession
from lavender_data.server.db.models import ApiKey

router = APIRouter(
    prefix="/cluster",
    tags=["cluster"],
)


class RegisterParams(BaseModel):
    node_url: str


@router.post("/register", dependencies=[Depends(AppAuth(cluster_auth=True))])
def register(
    params: RegisterParams,
    cluster: CurrentCluster,
    background_tasks: BackgroundTasks,
) -> None:
    if cluster is None:
        raise HTTPException(status_code=400, detail="Cluster not enabled")
    if not cluster.is_head:
        raise HTTPException(status_code=403, detail="Not allowed")
    background_tasks.add_task(cluster.on_register, params.node_url)


class DeregisterParams(BaseModel):
    node_url: str


@router.post("/deregister", dependencies=[Depends(AppAuth(cluster_auth=True))])
def deregister(
    params: DeregisterParams,
    cluster: CurrentCluster,
) -> None:
    if cluster is None:
        raise HTTPException(status_code=400, detail="Cluster not enabled")
    if not cluster.is_head:
        raise HTTPException(status_code=403, detail="Not allowed")
    cluster.on_deregister(params.node_url)


class HeartbeatParams(BaseModel):
    node_url: str


@router.post("/heartbeat", dependencies=[Depends(AppAuth(cluster_auth=True))])
def heartbeat(
    params: HeartbeatParams,
    cluster: CurrentCluster,
) -> None:
    if cluster is None:
        raise HTTPException(status_code=400, detail="Cluster not enabled")
    if not cluster.is_head:
        raise HTTPException(status_code=403, detail="Not allowed")
    cluster.on_heartbeat(params.node_url)


@router.get("/nodes", dependencies=[Depends(AppAuth(api_key_auth=True))])
def get_nodes(
    cluster: CurrentCluster,
) -> list[NodeStatus]:
    if cluster is None:
        raise HTTPException(status_code=400, detail="Cluster not enabled")
    if not cluster.is_head:
        raise HTTPException(status_code=403, detail="Not allowed")
    return cluster.get_node_statuses()


class ApiKeysAuthParams(BaseModel):
    api_key_id: str
    api_key_secret: str


@router.post("/get-api-keys", dependencies=[Depends(AppAuth(cluster_auth=True))])
def get_api_keys(
    params: ApiKeysAuthParams,
    cluster: CurrentCluster,
    session: DbSession,
):
    if cluster is None:
        raise HTTPException(status_code=400, detail="Cluster not enabled")
    if not cluster.is_head:
        raise HTTPException(status_code=403, detail="Not allowed")

    return session.exec(
        select(ApiKey).where(
            ApiKey.id == params.api_key_id,
            ApiKey.secret == params.api_key_secret,
        )
    ).one_or_none()
