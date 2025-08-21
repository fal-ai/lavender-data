import time
import threading
import base64
import hashlib
import secrets
from typing import Optional
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel

from lavender_data.logging import get_logger
from lavender_data.server.cache import CacheInterface, get_cache
from lavender_data.server.db.models import ApiKey


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


class NodeStatus(BaseModel):
    node_url: str
    last_heartbeat: Optional[float]
    is_head: bool


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

    def _post(self, node_url: str, path: str, json: dict = {}, timeout: float = 5.0):
        _path = path.lstrip("/")
        response = httpx.post(
            f"{node_url}/{_path}",
            json=json,
            headers=self._auth_header(),
            timeout=timeout,
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
    def head_post(self, path: str, json: dict, timeout: float = 5.0):
        return self._post(self.head_url, path, json, timeout)

    @only_worker
    def head_get(self, path: str):
        return self._get(self.head_url, path)

    def _key(self, key: str) -> str:
        return f"lavender_data:cluster:{key}"

    def _cache(self) -> CacheInterface:
        return next(get_cache())

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
            NodeStatus(
                node_url=node_url,
                last_heartbeat=self._last_heartbeat(node_url),
                is_head=node_url == self.head_url,
            )
            for node_url in self._node_urls(include_self=True)
        ]

    def get_api_key(self, api_key_id: str, api_key_secret: str) -> Optional[ApiKey]:
        api_key = self._post(
            self.head_url,
            "/cluster/get-api-keys",
            {
                "api_key_id": api_key_id,
                "api_key_secret": api_key_secret,
            },
        )
        if api_key is None:
            return None
        return ApiKey(**api_key)

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
    def start_prefetcher(self, iteration_id: str, params: dict):
        self.broadcast_post(f"/iterations/{iteration_id}/start-prefetcher", params)
