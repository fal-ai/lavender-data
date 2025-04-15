import time
from typing import Annotated, Optional, Type
from datetime import datetime
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import Depends
from pydantic import BaseModel
from sqlmodel import select, SQLModel

from lavender_data.server.cache import CacheInterface, get_cache
from lavender_data.server.db import DbSession, get_session
from lavender_data.server.db.models import (
    Dataset,
    DatasetColumn,
    Shardset,
    Shard,
    Iteration,
    IterationShardsetLink,
    ApiKey,
)


def only_head(f):
    def wrapper(self, *args, **kwargs):
        if self.is_head:
            return f(self, *args, **kwargs)
        else:
            raise RuntimeError(
                "This function is only allowed to be called on the head node"
            )

    return wrapper


def only_worker(f):
    def wrapper(self, *args, **kwargs):
        if not self.is_head:
            return f(self, *args, **kwargs)
        else:
            raise RuntimeError(
                "This function is only allowed to be called on the worker node"
            )

    return wrapper


class TaskKey(BaseModel):
    iteration_id: str
    cache_key: str
    indices: list[int]


class Cluster:
    def __init__(
        self,
        is_head: bool,
        head_url: str,
        broadcast_url: str,
    ):
        self.is_head = is_head
        self.head_url = head_url.rstrip("/")
        self.broadcast_url = broadcast_url.rstrip("/")

        if not self.is_head:
            self.register()
        else:
            self.accept_node(head_url)

    def _key(self, key: str) -> str:
        return f"lavender_data:cluster:{key}"

    def _cache(self) -> CacheInterface:
        return next(get_cache())

    def _db(self) -> DbSession:
        return next(get_session())

    def _dump_table(self, table: Type[SQLModel]) -> list[dict]:
        rows = self._db().exec(select(table)).all()
        dicts = []
        for row in rows:
            d = row.model_dump()
            for k, v in d.items():
                if isinstance(v, datetime):
                    d[k] = v.isoformat()
            dicts.append(d)
        return dicts

    def _node_urls(self) -> list[str]:
        return [
            url.decode("utf-8")
            for url in self._cache().lrange(self._key("node_urls"), 0, -1)
        ]

    def _wait_until_node_ready(
        self, node_url: str, timeout: float = 10.0, interval: float = 0.1
    ):
        start = time.time()
        while True:
            try:
                httpx.get(f"{node_url}/version")
                break
            except httpx.ConnectError:
                time.sleep(interval)
            if time.time() - start > timeout:
                raise RuntimeError(
                    f"Node {node_url} did not start in {timeout} seconds"
                )

    @only_head
    def accept_node(self, node_url: str):
        self._cache().lpush(self._key("node_urls"), node_url)
        if node_url != self.head_url:
            self._wait_until_node_ready(node_url)
            self.sync(node_url)

    @only_worker
    def register(self):
        httpx.post(
            f"{self.head_url}/cluster/register",
            json={"node_url": self.broadcast_url},
        )

    @only_head
    def sync(self, target_node_url: Optional[str] = None):
        json = {
            "datasets": self._dump_table(Dataset),
            "dataset_columns": self._dump_table(DatasetColumn),
            "shardsets": self._dump_table(Shardset),
            "shards": self._dump_table(Shard),
            "iterations": self._dump_table(Iteration),
            "iteration_shardset_links": self._dump_table(IterationShardsetLink),
            "api_keys": self._dump_table(ApiKey),
        }
        if target_node_url is None:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(httpx.post, f"{node_url}/cluster/sync", json=json)
                    for node_url in self._node_urls()
                ]
                for future in as_completed(futures):
                    future.result()
        else:
            httpx.post(f"{target_node_url}/cluster/sync", json=json)


cluster = None


def setup_cluster(
    is_head: bool,
    head_url: str,
    broadcast_url: str,
) -> Cluster:
    global cluster
    cluster = Cluster(is_head, head_url, broadcast_url)
    return cluster


def get_cluster() -> Optional[Cluster]:
    global cluster
    return cluster


CurrentCluster = Annotated[Optional[Cluster], Depends(get_cluster)]
