import time
import threading
from typing import Literal, Optional
from queue import Empty, Queue
from concurrent.futures import ThreadPoolExecutor, as_completed

from lavender_data.logging import get_logger
from lavender_data.server.distributed import get_cluster
from lavender_data.server.settings import get_settings
from lavender_data.server.cache import get_cache
from lavender_data.server.iteration.iteration_state import (
    IterationStateOps,
    IterationStateException,
)
from lavender_data.server.iteration.process import (
    ProcessNextSamplesException,
    gather_samples,
    organize_preprocessors,
    decollate,
)
from lavender_data.server.registries import Preprocessor
from lavender_data.serialize import serialize_sample


class NotFetchedYet(Exception):
    pass


class IterationPrefetcher:
    def __init__(
        self,
        iteration_id: str,
        state: IterationStateOps,
        max_retry_count: int,
        no_cache: bool,
        num_workers: int,
        prefetch_factor: int,
        in_order: bool,
    ):
        if max_retry_count < 0:
            raise ValueError("max_retry_count must be >= 0")

        self.iteration_id = iteration_id
        self.state = state
        self.max_retry_count = max_retry_count
        self.no_cache = no_cache
        self.num_workers = num_workers
        self.prefetch_factor = prefetch_factor
        self.in_order = in_order

        self.cache = next(get_cache())
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.cluster = get_cluster()

        self.fetching: dict[int, list[int]] = {}
        self.fetched: dict[int, dict[int, str]] = {}
        self.current: dict[int, int] = {}

        self.submit_threads: dict[int, threading.Thread] = {}
        self.process_threads: dict[int, list[threading.Thread]] = {}
        self.stop_event: dict[int, threading.Event] = {}
        self.all_submitted_event: dict[int, threading.Event] = {}
        self.done_event: dict[int, threading.Event] = {}

        self.process_queue = Queue()

        self._node_map: dict[int, dict[str, list[int]]] = {}
        self._sync_node_map_thread = None

    def _log(
        self,
        rank: int,
        message: str,
        level: Literal["debug", "info", "exception"] = "debug",
    ):
        if level == "debug":
            self.logger.debug(f"[{self.iteration_id} {rank=}] {message}")
        elif level == "info":
            self.logger.info(f"[{self.iteration_id} {rank=}] {message}")
        elif level == "exception":
            self.logger.exception(f"[{self.iteration_id} {rank=}] {message}")

    def _set_cache(
        self, rank: int, current: int, cache_key: str, content: Optional[bytes] = None
    ):
        if content is None:
            self.cache.expire(cache_key, self.settings.lavender_data_batch_cache_ttl)
        else:
            self.cache.set(
                cache_key, content, ex=self.settings.lavender_data_batch_cache_ttl
            )
        self.fetching[rank].remove(current)
        self.fetched[rank][current] = cache_key

        if self.cluster is not None and self.cluster.is_head:
            self._cleanup_node_map(rank, self.cluster.node_url, current)

    def _submit_prefetch(self, rank: int, queue: Queue):
        try:
            cache_key, params = self.state.get_next_samples(rank)
        except IterationStateException as e:
            if "No more indices to pop" in e.detail:
                raise StopIteration
            else:
                raise e
        except Exception as e:
            self._log(rank, f"Error prefetching {rank}: {e}")
            raise e

        self.fetching[rank].append(params.current)
        if self.cluster is not None and self.cluster.is_head:
            self.set_node_map(rank, self.cluster.node_url, params.current)

        if self.no_cache:
            self.cache.delete(cache_key)

        if self.cache.exists(cache_key):
            self._set_cache(rank, params.current, cache_key)
            return

        batch = gather_samples(params)
        if params.preprocessors is not None:
            preprocessors = organize_preprocessors(params.preprocessors)
            queue.put(
                (
                    rank,
                    params.current,
                    cache_key,
                    batch,
                    preprocessors,
                    0,
                    params.batch_size,
                )
            )
        else:
            content = serialize_sample(batch)
            self._set_cache(rank, params.current, cache_key, content)

    def _keep_submitting(
        self,
        rank: int,
        stop_event: threading.Event,
        all_submitted_event: threading.Event,
        queue: Queue,
    ) -> None:
        while not stop_event.is_set():
            while (
                len(self.upcoming_samples(rank))
                >= (self.prefetch_factor * self.num_workers)
                and not stop_event.is_set()
            ):
                time.sleep(0.01)

            if stop_event.is_set():
                break

            try:
                self._submit_prefetch(rank, queue)
            except StopIteration:
                break

        all_submitted_event.set()

    def _process_prefetch(
        self,
        rank: int,
        seq: int,
        cache_key: str,
        batch: dict,
        preprocessors: list[list[tuple[Preprocessor, dict]]],
        preprocessor_group_index: int,
        batch_size: int,
    ):
        _start = time.time()
        try:
            executor = ThreadPoolExecutor()
            futures = []
            for preprocessor, args in preprocessors[preprocessor_group_index]:
                futures.append(executor.submit(preprocessor.process, batch, **args))
            for future in as_completed(futures):
                batch.update(future.result())
            executor.shutdown()
            return batch
        except ProcessNextSamplesException as e:
            if cache_key:
                self._set_cache(
                    rank, seq, cache_key, f"processing_error:{e.json()}".encode("utf-8")
                )
        except Exception as e:
            if cache_key:
                self._set_cache(rank, seq, cache_key, f"error:{e}".encode("utf-8"))

    def _keep_prefetching(
        self,
        rank: int,
        stop_event: threading.Event,
        all_submitted_event: threading.Event,
        done_event: threading.Event,
        queue: Queue,
    ) -> None:
        while not stop_event.is_set() and not done_event.is_set():
            try:
                # rank, current, cache_key, batch, preprocessors, preprocessor_group_index, batch_size
                args = queue.get(timeout=1.0)
                next_batch = self._process_prefetch(*args)
                if next_batch is None:
                    # error occurred
                    continue

                if args[5] == len(args[4]) - 1:
                    # this one done
                    if args[6] == 0:
                        next_batch = decollate(next_batch)
                    self._set_cache(
                        args[0], args[1], args[2], serialize_sample(next_batch)
                    )
                    continue

                # proceed to next preprocessor group
                args[3] = next_batch
                args[5] += 1
                queue.put(args)
            except Empty:
                if all_submitted_event.is_set() and len(self.fetching[rank]) == 0:
                    self._log(rank, "Iteration finished")
                    break
                continue
            except Exception as e:
                self._log(rank, f"Error prefetching: {e}", level="exception")
                continue

        done_event.set()

    def get_next(self, rank: int, seq: Optional[int] = None) -> tuple[int, bytes]:
        try:
            if self.in_order and seq is None:
                current = self.current[rank]
                cache_key = self.fetched[rank].pop(current)
                self.current[rank] += 1
            elif seq is not None:
                current = seq
                # TODO possible infinite waiting
                cache_key = self.fetched[rank].pop(seq)
                self.current[rank] = current + 1
            else:
                current, cache_key = self.fetched[rank].popitem()
        except KeyError:
            if self.done_event[rank].is_set():
                raise StopIteration
            raise NotFetchedYet()

        content = self.cache.get(cache_key)
        if not content:
            raise Exception(f"Cache expired")
        if content.startswith(b"processing_error:"):
            raise ProcessNextSamplesException.from_json(content[17:])
        if content.startswith(b"error:"):
            raise Exception(content[6:].decode("utf-8"))

        return current, content

    def set_node_map(self, rank: int, node_url: str, seq: int) -> None:
        if rank not in self._node_map:
            self._node_map[rank] = {}
        if node_url not in self._node_map[rank]:
            self._node_map[rank][node_url] = []
        self._node_map[rank][node_url].append(seq)

    def get_node_map(self, rank: int) -> dict[str, list[int]]:
        return self._node_map.get(rank, {})

    def _cleanup_node_map(self, rank: int, node_url: str, current: int):
        if rank not in self._node_map:
            return
        if node_url not in self._node_map[rank]:
            return

        self._node_map[rank][node_url] = [
            seq for seq in self._node_map[rank][node_url] if seq > current
        ]

    def _sync_node_map(self):
        responses = self.cluster.broadcast_get(
            f"/iterations/{self.iteration_id}/prefetcher-current"
        )
        for node_url, currents in responses:
            if currents is None:
                continue

            for rank, current in currents.items():
                self._cleanup_node_map(int(rank), node_url, current)

    def _keep_syncing_node_map(
        self, stop_event: threading.Event, done_event: threading.Event
    ):
        while not stop_event.is_set() and not done_event.is_set():
            self._sync_node_map()
            time.sleep(5.0)

    def upcoming_samples(self, rank: int) -> list[int]:
        return self.fetching[rank] + list(self.fetched[rank].keys())

    def ranks(self) -> list[int]:
        return list(self.current.keys())

    def start(self, rank: int) -> None:
        self.current[rank] = 0
        self.fetching[rank] = []
        self.fetched[rank] = {}

        self.stop_event[rank] = threading.Event()
        self.done_event[rank] = threading.Event()
        self.all_submitted_event[rank] = threading.Event()

        self.submit_threads[rank] = threading.Thread(
            target=self._keep_submitting,
            args=(
                rank,
                self.stop_event[rank],
                self.all_submitted_event[rank],
                self.process_queue,
            ),
        )
        self.submit_threads[rank].start()

        self.process_threads[rank] = [
            threading.Thread(
                target=self._keep_prefetching,
                args=(
                    rank,
                    self.stop_event[rank],
                    self.all_submitted_event[rank],
                    self.done_event[rank],
                    self.process_queue,
                ),
            )
            for _ in range(self.num_workers)
        ]
        for thread in self.process_threads[rank]:
            thread.start()

        if (
            self.cluster is not None
            and self.cluster.is_head
            and self._sync_node_map_thread is None
        ):
            self._sync_node_map_thread = threading.Thread(
                target=self._keep_syncing_node_map,
                args=(self.stop_event[rank], self.done_event[rank]),
                daemon=True,
            )
            self._sync_node_map_thread.start()

    def join(self, rank: int) -> None:
        self.submit_threads[rank].join(timeout=5.0)
        if self.submit_threads[rank].is_alive():
            self._log(
                rank,
                f"Warning: Submit thread did not terminate within timeout",
            )
        for i, thread in enumerate(self.process_threads[rank]):
            thread.join(timeout=5.0)
            if thread.is_alive():
                self._log(
                    rank,
                    f"Warning: Thread {i} ({thread.name}) did not terminate within timeout",
                )

    def stop(self, rank: int) -> None:
        self._log(rank, "Stopping prefetcher threads")
        self.stop_event[rank].set()
        self.join(rank)
        if self._sync_node_map_thread is not None:
            self._sync_node_map_thread.join(timeout=5.0)
        self._log(rank, "Prefetcher stopped")

    def shutdown(self):
        for rank in self.ranks():
            self.stop(rank)

        self.logger.debug(f"[{self.iteration_id}] Prefetcher pool shutdown")


class IterationPrefetcherPool:
    def __init__(self):
        self.prefetchers: dict[str, IterationPrefetcher] = {}

    def get_prefetcher(self, iteration_id: str):
        return self.prefetchers[iteration_id]

    def create(
        self,
        iteration_id: str,
        state: IterationStateOps,
        max_retry_count: int,
        no_cache: bool,
        num_workers: int,
        prefetch_factor: int,
        in_order: bool,
    ):
        prefetcher = IterationPrefetcher(
            iteration_id,
            state,
            max_retry_count,
            no_cache,
            num_workers,
            prefetch_factor,
            in_order,
        )
        self.prefetchers[iteration_id] = prefetcher
        return prefetcher

    def shutdown(self):
        for prefetcher in self.prefetchers.values():
            prefetcher.shutdown()
