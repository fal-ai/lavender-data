import time
import threading
import base64
import hashlib
import secrets
from typing import Optional, Type
from datetime import datetime
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel
from sqlmodel import SQLModel, select, delete, insert, update

from lavender_data.logging import get_logger
from lavender_data.server.cache import CacheInterface, get_cache
from lavender_data.server.db import DbSession, get_session
from lavender_data.server.db.models import (
    Dataset,
    DatasetBase,
    DatasetColumn,
    DatasetColumnBase,
    Shardset,
    ShardsetBase,
    Shard,
    ShardBase,
    Iteration,
    IterationBase,
    IterationShardsetLink,
    ApiKey,
    ApiKeyBase,
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


class SyncParams(BaseModel):
    datasets: list[DatasetBase]
    dataset_columns: list[DatasetColumnBase]
    shardsets: list[ShardsetBase]
    shards: list[ShardBase]
    iterations: list[IterationBase]
    iteration_shardset_links: list[IterationShardsetLink]
    api_keys: list[ApiKeyBase]


class NodeStatus(BaseModel):
    node_url: str
    last_heartbeat: Optional[float]


def _dump(publics: list[SQLModel]) -> list[dict]:
    return [public.model_dump() for public in publics]


def _get_table_and_rows(
    params: SyncParams,
) -> list[tuple[Type[SQLModel], list[SQLModel]]]:
    return [
        (ApiKey, params.api_keys),
        (Dataset, params.datasets),
        (Shardset, params.shardsets),
        (DatasetColumn, params.dataset_columns),
        (Shard, params.shards),
        (Iteration, params.iterations),
        (IterationShardsetLink, params.iteration_shardset_links),
    ]


def _table_name(entity: SQLModel) -> str:
    if isinstance(entity, Dataset) or isinstance(entity, DatasetBase):
        return "datasets"
    elif isinstance(entity, DatasetColumn) or isinstance(entity, DatasetColumnBase):
        return "dataset_columns"
    elif isinstance(entity, Shardset) or isinstance(entity, ShardsetBase):
        return "shardsets"
    elif isinstance(entity, Shard) or isinstance(entity, ShardBase):
        return "shards"
    elif isinstance(entity, Iteration) or isinstance(entity, IterationBase):
        return "iterations"
    elif isinstance(entity, IterationShardsetLink):
        return "iteration_shardset_links"
    elif isinstance(entity, ApiKey) or isinstance(entity, ApiKeyBase):
        return "api_keys"
    else:
        raise ValueError(f"Unknown table: {entity.__class__.__name__}")


def to_http_basic_auth(username: str, password: str) -> dict:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


allowed_api_paths = [
    r"/datasets/(.+)/shardsets/(.+)/sync",
]


class Cluster:
    def __init__(
        self,
        head_url: str,
        node_url: str,
        secret: str,
        disable_auth: bool = False,
        heartbeat_interval: float = 10.0,
        heartbeat_threshold: int = 3,
    ):
        self.is_head = head_url == node_url
        self.head_url = head_url.rstrip("/")
        self.node_url = node_url.rstrip("/")
        self.secret = secret
        self.disable_auth = disable_auth
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_threshold = heartbeat_threshold
        self.api_key_note = "_CLUSTER"
        self.logger = get_logger(__name__)

    def start(self):
        if self.is_head:
            self.start_check_heartbeat()
        else:
            self.register()
            self.start_heartbeat()

    def _get_auth_password(self, salt: str) -> str:
        return hashlib.sha256(f"{salt}:{self.secret}".encode()).hexdigest()

    def is_valid_auth(self, salt: str, password: str) -> bool:
        return self._get_auth_password(salt) == password

    def _auth_header(self) -> dict:
        if self.disable_auth:
            return {}

        username = secrets.token_hex(16)  # salt
        password = self._get_auth_password(username)
        return to_http_basic_auth(username, password)

    def _post(self, node_url: str, path: str, json: dict = {}):
        _path = path.lstrip("/")
        response = httpx.post(
            f"{node_url}/{_path}", json=json, headers=self._auth_header()
        )
        if response.status_code == 401:
            raise RuntimeError(
                "Invalid cluster auth. Please check if LAVENDER_DATA_CLUSTER_SECRET is correct."
            )
        response.raise_for_status()
        return response.json()

    def _get(self, node_url: str, path: str) -> dict:
        _path = path.lstrip("/")
        response = httpx.get(
            f"{node_url}/{_path}",
            headers=self._auth_header(),
        )
        if response.status_code == 401:
            raise RuntimeError(
                "Invalid cluster auth. Please check if LAVENDER_DATA_CLUSTER_SECRET is correct."
            )
        response.raise_for_status()
        return response.json()

    @only_head
    def broadcast_post(self, path: str, json: dict) -> list[tuple[str, Optional[dict]]]:
        node_urls = self._node_urls()
        if len(node_urls) == 0:
            return []

        def _post(node_url: str, path: str, json: dict):
            try:
                return node_url, self._post(node_url, path, json)
            except Exception as e:
                self.logger.error(f"Failed to post to {node_url}: {e}")
                return node_url, None

        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    _post,
                    node_url=node_url,
                    path=path,
                    json=json,
                )
                for node_url in node_urls
            ]
            for future in as_completed(futures):
                results.append(future.result())
        return results

    @only_head
    def broadcast_get(self, path: str) -> list[tuple[str, Optional[dict]]]:
        node_urls = self._node_urls()
        if len(node_urls) == 0:
            return []

        def _get(node_url: str, path: str):
            try:
                return node_url, self._get(node_url, path)
            except Exception as e:
                self.logger.error(f"Failed to get from {node_url}: {e}")
                return node_url, None

        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    _get,
                    node_url=node_url,
                    path=path,
                )
                for node_url in node_urls
            ]
            for future in as_completed(futures):
                results.append(future.result())
        return results

    @only_worker
    def head_post(self, path: str, json: dict):
        return self._post(self.head_url, path, json)

    @only_worker
    def head_get(self, path: str):
        return self._get(self.head_url, path)

    def _key(self, key: str) -> str:
        return f"lavender_data:cluster:{key}"

    def _cache(self) -> CacheInterface:
        return next(get_cache())

    def _db(self) -> DbSession:
        return next(get_session())

    def _model_to_dict(self, model: SQLModel) -> dict:
        d = model.model_dump()
        for k, v in d.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat()
        return d

    def _dump_table(self, table: Type[SQLModel]) -> list[dict]:
        session = self._db()
        rows = session.exec(select(table)).all()
        dicts = [self._model_to_dict(row) for row in rows]
        session.close()
        return dicts

    def _node_urls(self, include_self: bool = False) -> list[str]:
        urls = [
            url.decode("utf-8")
            for url in self._cache().lrange(self._key("node_urls"), 0, -1)
        ]
        if include_self:
            urls.append(self.node_url)
        return urls

    def _wait_until_node_ready(
        self, node_url: str, timeout: float = 10.0, interval: float = 0.1
    ):
        start = time.time()
        while True:
            try:
                self._get(node_url, "/version")
                break
            except httpx.ConnectError:
                time.sleep(interval)
            if time.time() - start > timeout:
                raise RuntimeError(
                    f"Node {node_url} did not start in {timeout} seconds"
                )

    def get_node_statuses(self) -> list[NodeStatus]:
        return [
            NodeStatus(node_url=node_url, last_heartbeat=self._last_heartbeat(node_url))
            for node_url in self._node_urls(include_self=True)
        ]

    @only_worker
    def register(self):
        self.logger.info(f"Waiting for head node to be ready: {self.head_url}")
        self._wait_until_node_ready(self.head_url)
        self._post(self.head_url, "/cluster/register", {"node_url": self.node_url})

    @only_head
    def on_register(self, node_url: str):
        self._cache().lpush(self._key("node_urls"), node_url)
        if node_url != self.head_url:
            self._wait_until_node_ready(node_url)
            self.on_heartbeat(node_url)
            self.sync_initial(node_url)
            self.logger.info(f"Node {node_url} registered")

    @only_worker
    def deregister(self):
        self._post(self.head_url, "/cluster/deregister", {"node_url": self.node_url})

    @only_head
    def on_deregister(self, node_url: str):
        self._cache().lrem(self._key("node_urls"), 0, node_url)
        self.logger.info(f"Node {node_url} deregistered")

    @only_worker
    def heartbeat(self):
        self._post(self.head_url, "/cluster/heartbeat", {"node_url": self.node_url})

    @only_head
    def on_heartbeat(self, node_url: str):
        if node_url not in self._node_urls():
            self.on_register(node_url)
            return

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
                    self.logger.error(
                        f"Failed to send heartbeat to {self.head_url}: {e}"
                    )
                time.sleep(self.heartbeat_interval)

        self.heartbeat_thread = threading.Thread(target=_heartbeat, daemon=True)
        self.heartbeat_thread.start()

    def _last_heartbeat(self, node_url: str) -> Optional[float]:
        heartbeat = self._cache().get(self._key(f"heartbeat:{node_url}"))
        if heartbeat is None:
            return None
        return float(heartbeat)

    @only_head
    def start_check_heartbeat(self):
        def _check_heartbeat():
            while True:
                try:
                    for node_url in self._node_urls():
                        if node_url == self.node_url:
                            continue

                        heartbeat = self._last_heartbeat(node_url)
                        if heartbeat is None:
                            self.on_deregister(node_url)
                            continue

                        if (
                            time.time() - heartbeat
                            > self.heartbeat_threshold * self.heartbeat_interval
                        ):
                            self.on_deregister(node_url)
                except Exception as e:
                    self.logger.error(f"Error checking heartbeat: {e}")

                time.sleep(self.heartbeat_interval)

        self.check_heartbeat_thread = threading.Thread(
            target=_check_heartbeat, daemon=True
        )
        self.check_heartbeat_thread.start()

    @only_head
    def sync_initial(self, target_node_url: Optional[str] = None):
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
            self.broadcast_post("/cluster/sync", json)
        else:
            self._post(target_node_url, "/cluster/sync", json)

    @only_worker
    def on_sync_initial(self, params: SyncParams):
        session = self._db()

        for table, _ in reversed(_get_table_and_rows(params)):
            if isinstance(table, Shard):
                continue

            session.exec(delete(table))

        for table, rows in _get_table_and_rows(params):
            if isinstance(table, Shard):
                continue

            if len(rows) == 0:
                continue
            session.exec(insert(table).values(_dump(rows)))

        session.commit()
        session.close()

    def sync_changes(
        self,
        resources: list[SQLModel],
        delete: bool = False,
        target_node_url: Optional[str] = None,
    ):
        d = {
            "datasets": [],
            "dataset_columns": [],
            "shardsets": [],
            "shards": [],
            "iterations": [],
            "iteration_shardset_links": [],
            "api_keys": [],
        }

        for entity in resources:
            d[_table_name(entity)].append(self._model_to_dict(entity))

        _delete = "true" if delete else "false"
        if target_node_url is None:
            if self.is_head:
                self.broadcast_post(f"/cluster/sync-changes?delete={_delete}", d)
            else:
                self._post(self.head_url, f"/cluster/sync-changes?delete={_delete}", d)
        else:
            self._post(target_node_url, f"/cluster/sync-changes?delete={_delete}", d)

    def on_sync_changes(
        self,
        params: SyncParams,
        delete: bool = False,
    ):
        session = self._db()

        for table, rows in _get_table_and_rows(params):
            if isinstance(table, Shard):
                continue

            if len(rows) == 0:
                continue

            if delete:
                # delete
                session.exec(delete(table).where(table.id.in_([r.id for r in rows])))
            else:
                # upsert
                existings = session.exec(
                    select(table).where(table.id.in_([r.id for r in rows]))
                ).all()
                existing_ids = [e.id for e in existings]

                update_params = [r for r in rows if r.id in existing_ids]
                for r in update_params:
                    session.exec(
                        update(table).where(table.id == r.id).values(r.model_dump())
                    )

                insert_params = [r for r in rows if r.id not in existing_ids]
                if len(insert_params) > 0:
                    session.exec(insert(table).values(_dump(insert_params)))

        session.commit()
        session.close()

        if self.is_head:
            # propagate changes to other nodes
            self.sync_changes(
                [row for _, rows in _get_table_and_rows(params) for row in rows],
                delete,
            )
