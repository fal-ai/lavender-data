import time
import threading

from lavender_data.logging import get_logger
from lavender_data.server.settings import get_settings
from lavender_data.server.cache import get_cache
from lavender_data.server.iteration.iteration_state import (
    IterationState,
    IterationStateException,
)
from lavender_data.server.iteration.process import (
    process_next_samples,
    ProcessNextSamplesException,
)
from lavender_data.serialize import serialize_sample


class NotFetchedYet(Exception):
    pass


class IterationPrefetcher:
    def __init__(
        self,
        state: IterationState,
        max_retry_count: int,
        no_cache: bool,
        num_workers: int,
        prefetch_factor: int,
        in_order: bool,
    ):
        if max_retry_count < 0:
            raise ValueError("max_retry_count must be >= 0")

        self.state = state
        self.max_retry_count = max_retry_count
        self.no_cache = no_cache
        self.num_workers = num_workers
        self.prefetch_factor = prefetch_factor
        self.in_order = in_order

        self.cache = next(get_cache())
        self.settings = get_settings()
        self.logger = get_logger(__name__)

        self.fetched: dict[int, dict[int, str]] = {}
        self.current: dict[int, int] = {}

        self.threads: dict[int, list[threading.Thread]] = {}
        self.stop_event: dict[int, threading.Event] = {}
        self.done_event: dict[int, threading.Event] = {}

    def _log(self, rank: int, message: str):
        self.logger.debug(f"[{self.state.iteration_id} {rank=}] {message}")

    def _prefetch(self, rank: int):
        _start = time.time()
        cache_key = None
        try:
            cache_key, params = self.state.get_next_samples(rank)
            cache_ttl = self.settings.lavender_data_batch_cache_ttl

            if self.no_cache:
                self.cache.delete(cache_key)

            if self.cache.exists(cache_key):
                self.cache.expire(cache_key, cache_ttl)
                self.fetched[rank][params.current] = cache_key
            else:
                batch = process_next_samples(params, self.max_retry_count)
                content = serialize_sample(batch)
                self.cache.set(cache_key, content, ex=cache_ttl)
                self.fetched[rank][params.current] = cache_key
            self._log(
                rank, f"Prefetched {params.current} in {time.time() - _start:.2f}s"
            )
        except IterationStateException as e:
            if "No more indices to pop" in e.detail:
                self._log(rank, "Iteration finished")
                raise StopIteration
            elif cache_key:
                self.cache.set(cache_key, f"error:{e.detail}", ex=cache_ttl)
                self.fetched[rank][params.current] = cache_key
        except ProcessNextSamplesException as e:
            if cache_key:
                self.cache.set(cache_key, f"processing_error:{e.json()}", ex=cache_ttl)
                self.fetched[rank][params.current] = cache_key
        except Exception as e:
            if cache_key:
                self.cache.set(cache_key, f"error:{e}", ex=cache_ttl)
                self.fetched[rank][params.current] = cache_key

    def _keep_prefetching(
        self, rank: int, stop_event: threading.Event, done_event: threading.Event
    ) -> None:
        while not stop_event.is_set():
            while (
                len(self.fetched[rank]) >= (self.prefetch_factor * self.num_workers)
                and not stop_event.is_set()
            ):
                time.sleep(0.01)

            if stop_event.is_set():
                break

            try:
                self._prefetch(rank)
            except StopIteration:
                done_event.set()
                break

        self._log(rank, "Prefetcher finished")

    def get_next(self, rank: int) -> tuple[int, bytes]:
        try:
            if self.in_order:
                current = self.current[rank]
                cache_key = self.fetched[rank].pop(current)
                self.current[rank] += 1
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

    def start(self, rank: int) -> None:
        self.current[rank] = 0
        self.fetched[rank] = {}
        self.stop_event[rank] = threading.Event()
        self.done_event[rank] = threading.Event()
        self.threads[rank] = [
            threading.Thread(
                target=self._keep_prefetching,
                args=(rank, self.stop_event[rank], self.done_event[rank]),
            )
            for _ in range(self.num_workers)
        ]
        for thread in self.threads[rank]:
            thread.start()

    def join(self, rank: int) -> None:
        for i, thread in enumerate(self.threads[rank]):
            thread.join(timeout=5.0)
            if thread.is_alive():
                self._log(
                    rank,
                    f"Warning: Thread {i} ({thread.name}) did not terminate within timeout",
                )
                self._log(
                    rank,
                    f"Thread {i} status: alive={thread.is_alive()}, daemon={thread.daemon}",
                )

    def stop(self, rank: int) -> None:
        self._log(rank, "Stopping prefetcher threads")
        self.stop_event[rank].set()
        self.join(rank)
        self._log(rank, "Prefetcher stopped")

    def shutdown(self):
        for rank in list(self.threads.keys()):
            self.stop(rank)

        self.logger.debug(f"[{self.state.iteration_id}] Prefetcher pool shutdown")


class IterationPrefetcherPool:
    def __init__(self):
        self.prefetchers: dict[str, IterationPrefetcher] = {}

    def get_prefetcher(self, iteration_id: str):
        return self.prefetchers[iteration_id]

    def create(
        self,
        iteration_id: str,
        state: IterationState,
        max_retry_count: int,
        no_cache: bool,
        num_workers: int,
        prefetch_factor: int,
        in_order: bool,
    ):
        prefetcher = IterationPrefetcher(
            state, max_retry_count, no_cache, num_workers, prefetch_factor, in_order
        )
        self.prefetchers[iteration_id] = prefetcher
        return prefetcher

    def shutdown(self):
        for prefetcher in self.prefetchers.values():
            prefetcher.shutdown()
