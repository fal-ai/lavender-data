from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from lavender_data.server.distributed import CurrentCluster, SyncParams


router = APIRouter(
    prefix="/cluster",
    tags=["cluster"],
    dependencies=[],  # TODO cluster auth
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
def sync(
    params: SyncParams,
    cluster: CurrentCluster,
) -> None:
    if cluster.is_head:
        raise HTTPException(status_code=403, detail="Not allowed")
    cluster.on_sync(params)
