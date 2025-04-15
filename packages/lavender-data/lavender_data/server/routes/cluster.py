from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlmodel import SQLModel
from sqlmodel import delete, insert

from lavender_data.server.distributed import CurrentCluster
from lavender_data.server.db import DbSession
from lavender_data.server.db.models import (
    Dataset,
    DatasetPublic,
    DatasetColumn,
    DatasetColumnPublic,
    Shardset,
    ShardsetPublic,
    Shard,
    ShardPublic,
    Iteration,
    IterationPublic,
    IterationShardsetLink,
    ApiKey,
    ApiKeyPublic,
)

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
    background_tasks.add_task(cluster.accept_node, params.node_url)


class SyncParams(BaseModel):
    datasets: list[DatasetPublic]
    dataset_columns: list[DatasetColumnPublic]
    shardsets: list[ShardsetPublic]
    shards: list[ShardPublic]
    iterations: list[IterationPublic]
    iteration_shardset_links: list[IterationShardsetLink]
    api_keys: list[ApiKeyPublic]


def _dump(publics: list[SQLModel]) -> list[dict]:
    return [public.model_dump() for public in publics]


@router.post("/sync")
def sync(
    params: SyncParams,
    session: DbSession,
) -> None:
    session.begin()
    session.exec(delete(IterationShardsetLink))
    session.exec(delete(Iteration))
    session.exec(delete(Shard))
    session.exec(delete(DatasetColumn))
    session.exec(delete(Shardset))
    session.exec(delete(Dataset))
    session.exec(delete(ApiKey))

    session.exec(insert(ApiKey).values(_dump(params.api_keys)))
    session.exec(insert(Dataset).values(_dump(params.datasets)))
    session.exec(insert(Shardset).values(_dump(params.shardsets)))
    session.exec(insert(DatasetColumn).values(_dump(params.dataset_columns)))
    session.exec(insert(Shard).values(_dump(params.shards)))
    session.exec(insert(Iteration).values(_dump(params.iterations)))
    session.exec(
        insert(IterationShardsetLink).values(_dump(params.iteration_shardset_links))
    )
    session.commit()
