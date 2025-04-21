from abc import ABC, abstractmethod
import contextlib
import time
import numpy as np
import ujson as json
import hashlib
from typing import Optional, Annotated

from fastapi import HTTPException, Depends
from pydantic import BaseModel

try:
    import torch
except ImportError:
    torch = None

from lavender_data.logging import get_logger
from lavender_data.serialize import serialize_sample
from lavender_data.server.cache import CacheClient
from lavender_data.server.distributed import CurrentCluster
from lavender_data.server.db.models import (
    Shardset,
    Iteration,
    IterationPreprocessor,
    IterationFilter,
    IterationCollater,
)
from lavender_data.server.reader import (
    get_reader_instance,
    ShardInfo,
    MainShardInfo,
    GlobalSampleIndex,
)
from lavender_data.server.services.registries import (
    PreprocessorRegistry,
    FilterRegistry,
    CollaterRegistry,
)


from .shardsets import get_main_shardset, span


@contextlib.contextmanager
def np_seed(seed: int):
    state = np.random.get_state()
    np.random.seed(seed)
    try:
        yield
    finally:
        np.random.set_state(state)


class IterationStateException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


class InProgressIndex(BaseModel):
    index: int
    rank: int
    started_at: float


class Progress(BaseModel):
    total: int
    current: int
    inprogress: list[InProgressIndex]
    completed: int
    filtered: int
    failed: int


def _hash(o: object) -> str:
    return hashlib.sha256(
        json.dumps(o, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def get_iteration_hash(iteration: Iteration, dataset_id: Optional[str] = None) -> str:
    return _hash(
        {
            "dataset_id": dataset_id or iteration.dataset.id,
            "shardsets": [s.id for s in iteration.shardsets],
            "batch_size": iteration.batch_size,
            "collater": iteration.collater,
            "filters": iteration.filters,
            "preprocessors": iteration.preprocessors,
            "shuffle": iteration.shuffle,
            "shuffle_seed": iteration.shuffle_seed,
            "shuffle_block_size": iteration.shuffle_block_size,
            "replication_pg": iteration.replication_pg,
        }
    )


def set_iteration_hash(
    iteration_id: str,
    iteration_hash: str,
    ttl: int,
    cache: CacheClient,
) -> None:
    cache.set(f"iteration_hash:{iteration_hash}", iteration_id, ex=ttl)


def get_iteration_id_from_hash(
    iteration_hash: str, cache: CacheClient
) -> Optional[str]:
    value = cache.get(f"iteration_hash:{iteration_hash}")
    if value is None:
        return None
    return value.decode("utf-8")


class ProcessNextSamplesParams(BaseModel):
    current: int
    global_sample_indices: list[GlobalSampleIndex]
    samples: Optional[list[dict]] = None
    collater: Optional[IterationCollater] = None
    preprocessors: Optional[list[IterationPreprocessor]] = None
    batch_size: int


def process_next_samples(params: ProcessNextSamplesParams) -> bytes:
    reader = get_reader_instance()
    logger = get_logger(__name__)

    current = params.current
    global_sample_indices = params.global_sample_indices
    samples = params.samples
    collater = params.collater
    preprocessors = params.preprocessors
    batch_size = params.batch_size

    if samples is None:
        try:
            samples = [reader.get_sample(i) for i in global_sample_indices]
        except Exception as e:
            # TODO fault tolerance
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read samples: {e.__class__.__name__}({str(e)})",
            )

    try:
        batch = (
            CollaterRegistry.get(collater["name"]).collate(samples)
            if collater is not None
            else CollaterRegistry.get("default").collate(samples)
        )
    except Exception as e:
        logger.exception(f'Error in collater: {e.__class__.__name__}("{str(e)}")')
        raise HTTPException(
            status_code=400,
            detail=f'Error in collater: {e.__class__.__name__}("{str(e)}")',
        )

    if preprocessors is not None:
        try:
            batch = PreprocessorRegistry.process(
                [(p["name"], p["params"]) for p in preprocessors],
                batch,
                # TODO configurable max_workers
            )
        except Exception as e:
            msg = f'Error in preprocessor: {e.__class__.__name__}("{str(e)}")'
            logger.exception(msg)
            raise HTTPException(status_code=400, detail=msg)

    if batch_size == 0:
        _batch = {}
        for k, v in batch.items():
            if torch is not None and isinstance(v, torch.Tensor):
                _batch[k] = v.item()
            else:
                _batch[k] = v[0]
        batch = _batch

    batch["_lavender_data_indices"] = [i.index for i in global_sample_indices]
    batch["_lavender_data_current"] = current

    return serialize_sample(batch)


def process_next_samples_and_cache(
    params: ProcessNextSamplesParams,
    cache_key: str,
    cache_ttl: int,
    cache: CacheClient,
):
    logger = get_logger(__name__)
    try:
        content = process_next_samples(params)
        cache.set(cache_key, content, ex=cache_ttl)
    except Exception as e:
        logger.exception(f"Error processing next samples: {e}")
        cache.set(cache_key, f"error:{e}", ex=cache_ttl)


class IterationStateOps(ABC):
    @abstractmethod
    def exists(self) -> bool: ...

    @abstractmethod
    def pushback_inprogress(self) -> None: ...

    @abstractmethod
    def complete(self, index: int) -> None: ...

    @abstractmethod
    def filtered(self, index: int) -> None: ...

    @abstractmethod
    def failed(self, index: int) -> None: ...

    @abstractmethod
    def next_item(self, rank: int) -> GlobalSampleIndex: ...

    @abstractmethod
    def get_ranks(self) -> list[int]: ...

    @abstractmethod
    def get_progress(self) -> Progress: ...

    @abstractmethod
    def get_next_samples(self, rank: int) -> tuple[str, ProcessNextSamplesParams]: ...


class IterationState(IterationStateOps):
    def __init__(self, iteration_id: str, cache: CacheClient):
        self.iteration_id = iteration_id
        self.cache = cache

    def _key(self, key: str) -> str:
        return f"{self.iteration_id}:{key}"

    def _set_iteration_info(
        self,
        iteration: Iteration,
    ) -> None:
        uid_column = next(
            (
                c
                for c in iteration.dataset.columns
                if c.name == iteration.dataset.uid_column_name
            ),
            None,
        )
        if uid_column is None:
            raise IterationStateException(
                f'uid column "{iteration.dataset.uid_column_name}" not found in dataset "{iteration.dataset.id}"'
            )

        with self.cache.pipeline() as pipe:
            pipe.set(self._key("batch_size"), iteration.batch_size)
            pipe.set(self._key("total"), iteration.total)
            pipe.set(self._key("uid_column_name"), iteration.dataset.uid_column_name)
            pipe.set(self._key("uid_column_type"), uid_column.type)
            pipe.delete(self._key("completed"))
            pipe.delete(self._key("pushed"))
            pipe.delete(self._key("filtered"))
            pipe.delete(self._key("failed"))
            pipe.incr(self._key("completed"), 0)
            pipe.incr(self._key("pushed"), 0)
            pipe.incr(self._key("filtered"), 0)
            pipe.incr(self._key("failed"), 0)
            if iteration.shuffle:
                pipe.set(self._key("shuffle_seed"), iteration.shuffle_seed)
                pipe.set(self._key("shuffle_block_size"), iteration.shuffle_block_size)

            if iteration.replication_pg is not None:
                pipe.set(
                    self._key("replication_pg"), json.dumps(iteration.replication_pg)
                )

            if iteration.preprocessors is not None:
                pipe.set(
                    self._key("preprocessors"), json.dumps(iteration.preprocessors)
                )

            if iteration.filters is not None:
                pipe.set(self._key("filters"), json.dumps(iteration.filters))

            if iteration.collater is not None:
                pipe.set(self._key("collater"), json.dumps(iteration.collater))

            pipe.set(self._key("iteration_hash"), get_iteration_hash(iteration))
            pipe.execute()

    def _cache_key(self, indices: list[int]) -> str:
        return _hash(
            {
                "iteration_hash": self.cache.get(self._key("iteration_hash")).decode(
                    "utf-8"
                ),
                "indices": indices,
            }
        )

    def _count_batch(self) -> int:
        batch_count = self.cache.incr(self._key("batch_count"), 1)
        return int(batch_count)

    def _batch_size(self) -> int:
        return int(self.cache.get(self._key("batch_size")))

    def _preprocessors(self) -> Optional[list[IterationPreprocessor]]:
        v = self.cache.get(self._key("preprocessors"))
        if v is None:
            return None
        return json.loads(v)

    def _filters(self) -> Optional[list[IterationFilter]]:
        v = self.cache.get(self._key("filters"))
        if v is None:
            return None
        return json.loads(v)

    def _collater(self) -> Optional[IterationCollater]:
        v = self.cache.get(self._key("collater"))
        if v is None:
            return None
        return json.loads(v)

    def _set_shardsets_info(self, shardsets: list[Shardset]) -> None:
        with self.cache.pipeline() as pipe:
            pipe.rpush(
                self._key("shardsets"),
                *[shardset.id for shardset in shardsets],
            )
            for shardset in shardsets:
                pipe.set(
                    self._key(f"shardsets:{shardset.id}:columns"),
                    json.dumps(
                        {column.name: column.type for column in shardset.columns}
                    ),
                )
                shards = sorted(shardset.shards, key=lambda s: s.index)
                pipe.rpush(
                    self._key(f"shardsets:{shardset.id}:samples"),
                    *[shard.samples for shard in shards],
                )
                pipe.rpush(
                    self._key(f"shardsets:{shardset.id}:location"),
                    *[shard.location for shard in shards],
                )
                pipe.rpush(
                    self._key(f"shardsets:{shardset.id}:format"),
                    *[shard.format for shard in shards],
                )
                pipe.rpush(
                    self._key(f"shardsets:{shardset.id}:filesize"),
                    *[shard.filesize for shard in shards],
                )
                pipe.execute()

    def _set_main_shardset_info(
        self, shardset: Shardset, shuffle: bool, shuffle_seed: int
    ) -> None:
        shards = sorted(shardset.shards, key=lambda s: s.index)

        last_end = 0
        shard_sample_ranges = []
        for shard in shards:
            shard_sample_ranges.append(
                {
                    "shard": shard.index,
                    "start": last_end,
                    "end": last_end + shard.samples - 1,
                }
            )
            last_end += shard.samples

        if shuffle:
            with np_seed(shuffle_seed):
                np.random.shuffle(shard_sample_ranges)

        with self.cache.pipeline() as pipe:
            pipe.set(self._key("main_shardset"), shardset.id)
            shard_samples = []
            for shard_sample_range in shard_sample_ranges:
                shard_samples.extend(
                    [shard_sample_range["start"], shard_sample_range["end"]]
                )
            pipe.rpush(self._key("shard_samples"), *shard_samples)
            pipe.execute()

    def _get_shard_info(self, shardset_id: str, shard_index: int) -> ShardInfo:
        with self.cache.pipeline() as pipe:
            pipe.get(self._key(f"shardsets:{shardset_id}:columns"))
            pipe.lindex(self._key(f"shardsets:{shardset_id}:samples"), shard_index)
            pipe.lindex(self._key(f"shardsets:{shardset_id}:location"), shard_index)
            pipe.lindex(self._key(f"shardsets:{shardset_id}:format"), shard_index)
            pipe.lindex(self._key(f"shardsets:{shardset_id}:filesize"), shard_index)
            [columns, samples, location, format, filesize] = pipe.execute()
        return ShardInfo(
            shardset_id=shardset_id,
            columns=json.loads(columns),
            index=shard_index,
            samples=int(samples),
            location=location.decode("utf-8"),
            format=format.decode("utf-8"),
            filesize=int(filesize),
        )

    def _push_indices(self, rank: int) -> None:
        retrieved_shuffle_seed = self.cache.get(self._key("shuffle_seed"))
        shuffle = retrieved_shuffle_seed is not None
        shuffle_seed = int(retrieved_shuffle_seed) if shuffle else None
        block_size = (
            int(self.cache.get(self._key("shuffle_block_size"))) if shuffle else 1
        )

        indices = []
        for _ in range(block_size):
            retrieved = self.cache.lpop(self._key("shard_samples"), 2)
            if retrieved is None:
                continue
            start = int(retrieved[0])
            end = int(retrieved[1])
            indices.extend(range(start, end + 1))

        if len(indices) == 0:
            return

        # TODO shuffle leftovers with more randomness
        if shuffle:
            with np_seed(shuffle_seed):
                np.random.shuffle(indices)

        replication_pg = self.cache.get(self._key("replication_pg"))
        if replication_pg is not None:
            replication_pg = json.loads(replication_pg)

        with self.cache.pipeline() as pipe:
            if replication_pg is not None:
                rank_pg = None
                for pg in replication_pg:
                    if rank in pg:
                        rank_pg = pg
                        break
                if rank_pg is None:
                    raise IterationStateException(
                        f"Replication pg not found for rank {rank}"
                    )
                for rank in rank_pg:
                    pipe.rpush(self._key(f"indices:{rank}"), *indices)
            else:
                pipe.rpush(self._key(f"indices:{rank}"), *indices)

            pipe.incr(self._key("pushed"), len(indices))
            pipe.execute()

    def _pop_index(self, rank: int) -> int:
        retrieved = self.cache.lpop(self._key(f"indices:{rank}"), 1)
        if retrieved is None:
            self._push_indices(rank)
            retrieved = self.cache.lpop(self._key(f"indices:{rank}"), 1)

        if retrieved is None:
            raise IterationStateException("No more indices to pop")

        index = int(retrieved[0])
        now = time.time()
        self.cache.hset(self._key("inprogress"), index, f"{rank}:{now}")

        return index

    def _get_shards_from_index(
        self, index: int
    ) -> tuple[MainShardInfo, list[ShardInfo]]:
        main_shardset_id = self.cache.get(self._key("main_shardset")).decode("utf-8")
        shard_samples = [
            int(s)
            for s in self.cache.lrange(
                self._key(f"shardsets:{main_shardset_id}:samples"), 0, -1
            )
        ]
        shard_index, sample_index = span(index, shard_samples)
        main_shard = MainShardInfo(
            sample_index=sample_index,
            **self._get_shard_info(main_shardset_id, shard_index).model_dump(),
        )

        shardsets = [
            s.decode("utf-8") for s in self.cache.lrange(self._key("shardsets"), 0, -1)
        ]
        shards: list[ShardInfo] = [
            self._get_shard_info(shardset_id, shard_index)
            for shardset_id in shardsets
            if shardset_id != main_shardset_id
        ]

        if main_shard is None:
            raise IterationStateException("Main shard not found")

        return main_shard, shards

    def _get_inprogress(self) -> list[InProgressIndex]:
        return [
            InProgressIndex(
                index=int(k.decode("utf-8")),
                rank=int(v.decode("utf-8").split(":")[0]),
                started_at=float(v.decode("utf-8").split(":")[1]),
            )
            for k, v in self.cache.hgetall(self._key("inprogress")).items()
        ]

    def _get_current(self) -> int:
        pushed = self.cache.incr(self._key("pushed"), 0)
        inqueue = 0

        replication_pg = self.cache.get(self._key("replication_pg"))
        if replication_pg is not None:
            replication_pg = json.loads(replication_pg)

        if replication_pg is not None:
            with self.cache.pipeline() as pipe:
                for pg in replication_pg:
                    pipe.llen(self._key(f"indices:{pg[0]}"))
                inqueue = sum(pipe.execute())
        else:
            ranks = self.get_ranks()
            with self.cache.pipeline() as pipe:
                for rank in ranks:
                    pipe.llen(self._key(f"indices:{rank}"))
                inqueue = sum(pipe.execute())

        return pushed - inqueue

    def exists(self) -> bool:
        return self.cache.exists(self._key("total"))

    def init(self, iteration: Iteration) -> None:
        with self.cache.lock(self._key("init")):
            if self.exists():
                return

            shardsets = [s for s in iteration.shardsets if len(s.shards) > 0]

            if len(shardsets) == 0:
                # never happens unless all shardsets have 0 samples
                raise IterationStateException(
                    "Please add at least one shardset to the dataset. "
                    if len(iteration.shardsets) == 0
                    else (
                        "Please add at least one shard to the shardset. "
                        ", ".join(
                            [
                                f"{s.id} ({s.location}) - {len(s.shards)} shards"
                                for s in iteration.shardsets
                            ]
                        )
                    )
                )

            main_shardset = get_main_shardset(shardsets)

            self._set_iteration_info(iteration)
            self._set_shardsets_info(shardsets)
            self._set_main_shardset_info(
                main_shardset, iteration.shuffle, iteration.shuffle_seed
            )

    def pushback_inprogress(self) -> None:
        for inprogress in self._get_inprogress():
            self.cache.lpush(self._key(f"indices:{inprogress.rank}"), inprogress.index)
        self.cache.delete(self._key("inprogress"))

    def complete(self, index: int) -> None:
        # TODO clean up cache on done
        removed = self.cache.hdel(self._key("inprogress"), index)
        if removed != 1:
            return
        self.cache.incr(self._key("completed"), 1)

    def filtered(self, index: int) -> None:
        removed = self.cache.hdel(self._key("inprogress"), index)
        if removed != 1:
            return
        self.cache.incr(self._key("filtered"), 1)

    def failed(self, index: int) -> None:
        removed = self.cache.hdel(self._key("inprogress"), index)
        if removed != 1:
            return
        self.cache.incr(self._key("failed"), 1)

    def next_item(self, rank: int) -> GlobalSampleIndex:
        with self.cache.pipeline() as pipe:
            pipe.get(self._key("uid_column_name"))
            pipe.get(self._key("uid_column_type"))
            [uid_column_name, uid_column_type] = pipe.execute()
        uid_column_name = uid_column_name.decode("utf-8")
        uid_column_type = uid_column_type.decode("utf-8")

        with self.cache.lock(f"next_item:{self.iteration_id}"):
            index = self._pop_index(rank)

        main_shard, feature_shards = self._get_shards_from_index(index)
        return GlobalSampleIndex(
            index=index,
            uid_column_name=uid_column_name,
            uid_column_type=uid_column_type,
            main_shard=main_shard,
            feature_shards=feature_shards,
        )

    def get_ranks(self) -> list[int]:
        return [
            int(k.decode("utf-8").split("indices:", 1)[1])
            for k in self.cache.keys(self._key("indices:*"))
        ]

    def get_progress(self) -> Progress:
        total = int(self.cache.get(self._key("total")))
        current = self._get_current()
        inprogress = self._get_inprogress()
        with self.cache.pipeline() as pipe:
            pipe.incr(self._key("completed"), 0)
            pipe.incr(self._key("filtered"), 0)
            pipe.incr(self._key("failed"), 0)
            [completed, filtered, failed] = pipe.execute()
        completed = int(completed)
        filtered = int(filtered)
        failed = int(failed)

        return Progress(
            current=current,
            inprogress=inprogress,
            completed=completed,
            filtered=filtered,
            failed=failed,
            total=total,
        )

    def get_next_samples(
        self,
        rank: int,
    ) -> tuple[str, ProcessNextSamplesParams]:
        reader = get_reader_instance()
        logger = get_logger(__name__)

        batch_size = self._batch_size()
        filters = self._filters()

        global_sample_indices = []
        samples = []
        while len(samples) < max(batch_size, 1):
            next_item = self.next_item(rank)

            try:
                sample = reader.get_sample(next_item)
            except Exception as e:
                # TODO fault tolerance
                self.failed(next_item.index)
                msg = f"Failed to read sample {next_item.index} (sample {next_item.main_shard.sample_index} of shard {next_item.main_shard.index}): {e.__class__.__name__}({str(e)})"
                logger.exception(msg)
                raise HTTPException(status_code=400, detail=msg)

            should_include = True
            if filters is not None:
                for f in filters:
                    should_include = FilterRegistry.get(f["name"]).filter(
                        sample, **f["params"]
                    )
                    if not should_include:
                        break

            if not should_include:
                self.filtered(next_item.index)
                continue

            global_sample_indices.append(next_item)
            samples.append(sample)

        cache_key = self._cache_key([i.index for i in global_sample_indices])

        return cache_key, ProcessNextSamplesParams(
            current=self._count_batch(),
            global_sample_indices=global_sample_indices,
            samples=samples,
            collater=self._collater(),
            preprocessors=self._preprocessors(),
            batch_size=self._batch_size(),
        )


class IterationStateClusterOps(IterationStateOps):
    def __init__(self, iteration_id: str, cluster: CurrentCluster):
        self.iteration_id = iteration_id
        self.cluster = cluster

    def _head(self, path: str, json: dict) -> dict:
        try:
            return self.cluster.head_post(
                f"/iterations/{self.iteration_id}/state/{path}", json
            )
        except Exception as e:
            raise IterationStateException(str(e))

    def exists(self) -> bool:
        return self._head("exists", {})

    def pushback_inprogress(self) -> None:
        return self._head("pushback_inprogress", {})

    def complete(self, index: int) -> None:
        return self._head("complete", {"index": index})

    def filtered(self, index: int) -> None:
        return self._head("filtered", {"index": index})

    def failed(self, index: int) -> None:
        return self._head("failed", {"index": index})

    def next_item(self, rank: int) -> GlobalSampleIndex:
        return GlobalSampleIndex(**self._head("next_item", {"rank": rank}))

    def get_ranks(self) -> list[int]:
        return self._head("get_ranks", {})

    def get_progress(self) -> Progress:
        return Progress(**self._head("get_progress", {}))

    def get_next_samples(self, rank: int) -> tuple[str, ProcessNextSamplesParams]:
        cache_key, params = self._head("get_next_samples", {"rank": rank})
        return cache_key, ProcessNextSamplesParams(**params)


def set_cluster_sync(
    iteration_id: str,
    cache: CacheClient,
    cluster: CurrentCluster,
):
    cache.set(f"cluster_sync:{iteration_id}", "true")
    if cluster is not None and cluster.is_head:
        try:
            cluster.broadcast_post(
                f"/iterations/{iteration_id}/state/set-cluster-sync", {}
            )
        except Exception as e:
            raise IterationStateException(str(e))


def is_cluster_sync(
    iteration_id: str,
    cache: CacheClient,
) -> bool:
    return cache.get(f"cluster_sync:{iteration_id}") == b"true"


def get_iteration_id_from_hash_from_head(
    iteration_hash: str, cluster: CurrentCluster, timeout: int = 10
) -> Optional[str]:
    start = time.time()
    while True:
        try:
            iteration_id = cluster.head_get(
                f"/iterations/iteration-id-from-hash?iteration_hash={iteration_hash}",
            )
            if iteration_id is None:
                raise IterationStateException("Iteration not found")
            return iteration_id
        except Exception as e:
            if time.time() - start > timeout:
                raise IterationStateException(str(e))
            time.sleep(0.1)


def get_iteration_state(
    iteration_id: str, cache: CacheClient, cluster: CurrentCluster
) -> IterationState:
    state = None

    if is_cluster_sync(iteration_id, cache):
        if cluster is None:
            raise HTTPException(status_code=400, detail="Cluster not found")
        if not cluster.is_head:
            state = IterationStateClusterOps(iteration_id, cluster)

    if state is None:
        state = IterationState(iteration_id, cache)

    if not state.exists():
        raise HTTPException(status_code=404, detail="Iteration not initialized")

    return state


CurrentIterationState = Annotated[IterationStateOps, Depends(get_iteration_state)]
