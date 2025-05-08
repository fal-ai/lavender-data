from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel

from lavender_data.server.distributed import CurrentCluster
from lavender_data.server.distributed.cluster import SyncParams, NodeStatus
from lavender_data.server.auth import AppAuth

router = APIRouter(
    prefix="/cluster",
    tags=["cluster"],
    dependencies=[Depends(AppAuth(cluster_auth=True))],
)


class RegisterParams(BaseModel):
    node_url: str


@router.post("/register")
def register(
    params: RegisterParams,
    cluster: CurrentCluster,
    background_tasks: BackgroundTasks,
) -> None:
    if not cluster.is_head:
        raise HTTPException(status_code=403, detail="Not allowed")
    background_tasks.add_task(cluster.on_register, params.node_url)


class DeregisterParams(BaseModel):
    node_url: str


@router.post("/deregister")
def deregister(
    params: DeregisterParams,
    cluster: CurrentCluster,
) -> None:
    if not cluster.is_head:
        raise HTTPException(status_code=403, detail="Not allowed")
    cluster.on_deregister(params.node_url)


class HeartbeatParams(BaseModel):
    node_url: str


@router.post("/heartbeat")
def heartbeat(
    params: HeartbeatParams,
    cluster: CurrentCluster,
) -> None:
    if not cluster.is_head:
        raise HTTPException(status_code=403, detail="Not allowed")
    cluster.on_heartbeat(params.node_url)


@router.post("/sync")
def sync_initial(
    params: SyncParams,
    cluster: CurrentCluster,
) -> None:
    if cluster.is_head:
        raise HTTPException(status_code=403, detail="Not allowed")
    cluster.on_sync_initial(params)


@router.post("/sync-changes")
def sync_changes(
    params: SyncParams,
    cluster: CurrentCluster,
    delete: bool = False,
) -> None:
    cluster.on_sync_changes(params, delete)


@router.get("/nodes")
def get_nodes(
    cluster: CurrentCluster,
) -> list[NodeStatus]:
    if not cluster.is_head:
        raise HTTPException(status_code=403, detail="Not allowed")
    return cluster.get_node_statuses()
