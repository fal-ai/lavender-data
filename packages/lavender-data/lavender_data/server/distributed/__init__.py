import time
import threading
from typing import Annotated, Optional, Type
from datetime import datetime
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import Depends
from pydantic import BaseModel
from sqlmodel import SQLModel, select, delete, insert

from lavender_data.logging import get_logger
from lavender_data.server.cache import CacheInterface, get_cache
from lavender_data.server.db import DbSession, get_session
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

logger = get_logger(__name__)


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


class Cluster:
    def __init__(
        self,
        is_head: bool,
        head_url: str,
        node_url: str,
        heartbeat_interval: float = 10.0,
        heartbeat_threshold: int = 3,
    ):
        self.is_head = is_head
        self.head_url = head_url.rstrip("/")
        self.node_url = node_url.rstrip("/")
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_threshold = heartbeat_threshold

        if self.is_head:
            self.on_register(head_url)
            self.start_check_heartbeat()
        else:
            self.register()
            self.start_heartbeat()

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

    @only_worker
    def register(self):
        logger.info(f"Waiting for head node to be ready: {self.head_url}")
        self._wait_until_node_ready(self.head_url)
        httpx.post(
            f"{self.head_url}/cluster/register",
            json={"node_url": self.node_url},
        )

    @only_head
    def on_register(self, node_url: str):
        self._cache().lpush(self._key("node_urls"), node_url)
        if node_url != self.head_url:
            self._wait_until_node_ready(node_url)
            self.on_heartbeat(node_url)
            self.sync(node_url)
            logger.info(f"Node {node_url} registered")

    @only_worker
    def deregister(self):
        httpx.post(
            f"{self.head_url}/cluster/deregister",
            json={"node_url": self.node_url},
        )

    @only_head
    def on_deregister(self, node_url: str):
        self._cache().lrem(self._key("node_urls"), 0, node_url)
        logger.info(f"Node {node_url} deregistered")

    @only_worker
    def heartbeat(self):
        httpx.post(
            f"{self.head_url}/cluster/heartbeat",
            json={"node_url": self.node_url},
        )

    @only_head
    def on_heartbeat(self, node_url: str):
        self._cache().set(
            self._key(f"heartbeat:{node_url}"), time.time(), ex=24 * 60 * 60
        )

    @only_worker
    def start_heartbeat(self):
        def _heartbeat():
            while True:
                try:
                    self.heartbeat()
                except Exception as e:
                    logger.error(f"Error sending heartbeat: {e}")
                time.sleep(self.heartbeat_interval)

        self.heartbeat_thread = threading.Thread(target=_heartbeat, daemon=True)
        self.heartbeat_thread.start()

    @only_worker
    def stop_heartbeat(self):
        self.heartbeat_thread.join()

    @only_head
    def start_check_heartbeat(self):
        def _check_heartbeat():
            while True:
                try:
                    for node_url in self._node_urls():
                        heartbeat = self._cache().get(
                            self._key(f"heartbeat:{node_url}")
                        )
                        if heartbeat is None:
                            self.on_deregister(node_url)
                            continue

                        if (
                            time.time() - float(heartbeat)
                            > self.heartbeat_threshold * self.heartbeat_interval
                        ):
                            self.on_deregister(node_url)
                except Exception as e:
                    logger.error(f"Error checking heartbeat: {e}")

                time.sleep(self.heartbeat_interval)

        self.check_heartbeat_thread = threading.Thread(
            target=_check_heartbeat, daemon=True
        )
        self.check_heartbeat_thread.start()

    @only_head
    def stop_check_heartbeat(self):
        self.check_heartbeat_thread.join()

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

    @only_worker
    def on_sync(self, params: SyncParams):
        session = self._db()
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


cluster = None


def setup_cluster(
    is_head: bool,
    head_url: str,
    node_url: str,
) -> Cluster:
    global cluster
    cluster = Cluster(is_head, head_url, node_url)
    return cluster


def get_cluster() -> Optional[Cluster]:
    global cluster
    return cluster


CurrentCluster = Annotated[Optional[Cluster], Depends(get_cluster)]
