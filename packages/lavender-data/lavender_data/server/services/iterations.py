import contextlib
import time
import numpy as np
import ujson as json
from typing import Optional, Any

from pydantic import BaseModel
from lavender_data.server.cache import RedisClient
from lavender_data.server.db.models import (
    Iteration,
    Shardset,
)
from lavender_data.server.reader import ShardInfo, MainShardInfo, GetSampleParams


from .shardsets import get_main_shardset, span


@contextlib.contextmanager
def np_seed(seed: int):
    state = np.random.get_state()
    np.random.seed(seed)
    try:
        yield
    finally:
        np.random.set_state(state)


class IterationStateException(Exception):
    pass


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


class IterationState:
    _instances = {}

    def __new__(cls, iteration_id: str, cache: RedisClient):
        if iteration_id not in cls._instances:
            cls._instances[iteration_id] = super().__new__(cls)
        return cls._instances[iteration_id]

    def __init__(self, iteration_id: str, cache: RedisClient):
        self.iteration_id = iteration_id
        self.cache = cache
        self.mem_cache = {}

    def _key(self, key: str) -> str:
        return f"{self.iteration_id}:{key}"

    def _get(self, key: str) -> Optional[Any]:
        if key in self.mem_cache:
            return self.mem_cache[key]
        value = self.cache.get(self._key(key))
        self.mem_cache[key] = value
        return value

    def _list_all(self, key: str) -> list[Any]:
        if key in self.mem_cache:
            return self.mem_cache[key]
        value = self.cache.lrange(self._key(key), 0, -1)
        self.mem_cache[key] = value
        return value

    def _set_iteration_info(self, iteration: Iteration) -> None:
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

        with self.pipeline() as pipe:
            pipe.set(self._key("batch_size"), iteration.batch_size)
            pipe.set(self._key("total"), iteration.total)
            pipe.set(self._key("uid_column_name"), iteration.dataset.uid_column_name)
            pipe.set(self._key("uid_column_type"), uid_column.type)
            pipe.set(self._key("completed"), 0)
            pipe.set(self._key("pushed"), 0)
            pipe.set(self._key("filtered"), 0)
            pipe.set(self._key("failed"), 0)
            if iteration.shuffle:
                pipe.set(self._key("shuffle_seed"), iteration.shuffle_seed)
                pipe.set(self._key("shuffle_block_size"), iteration.shuffle_block_size)

            if iteration.replication_pg is not None:
                pipe.set(
                    self._key("replication_pg"), json.dumps(iteration.replication_pg)
                )

            if iteration.preprocessor is not None:
                pipe.set(self._key("preprocessor"), iteration.preprocessor)

            if iteration.filter is not None:
                pipe.set(self._key("filter"), iteration.filter)

            if iteration.collater is not None:
                pipe.set(self._key("collater"), iteration.collater)

    def _set_shardsets_info(self, shardsets: list[Shardset]) -> None:
        with self.pipeline() as pipe:
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
                pipe.rpush(
                    self._key(f"shardsets:{shardset.id}:samples"),
                    *[shard.samples for shard in shardset.shards],
                )
                pipe.rpush(
                    self._key(f"shardsets:{shardset.id}:location"),
                    *[shard.location for shard in shardset.shards],
                )
                pipe.rpush(
                    self._key(f"shardsets:{shardset.id}:format"),
                    *[shard.format for shard in shardset.shards],
                )
                pipe.rpush(
                    self._key(f"shardsets:{shardset.id}:filesize"),
                    *[shard.filesize for shard in shardset.shards],
                )

    def _set_main_shardset_info(
        self, shardset: Shardset, shuffle: bool, shuffle_seed: int
    ) -> None:
        shards = shardset.shards
        if shuffle:
            with np_seed(shuffle_seed):
                np.random.shuffle(shards)

        last_end = 0
        shard_samples = []
        for shard in shards:
            shard_samples.extend([last_end, last_end + shard.samples - 1])
            last_end += shard.samples

        with self.pipeline() as pipe:
            pipe.set(self._key("main_shardset"), shardset.id)
            pipe.rpush(self._key("shard_samples"), *shard_samples)

    def _get_shard_info(self, shardset_id: str, shard_index: int) -> ShardInfo:
        pipe = self.cache.pipeline()
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

    def exists(self) -> bool:
        return self.cache.exists(self._key("total"))

    @contextlib.contextmanager
    def pipeline(self):
        pipe = self.cache.pipeline()
        try:
            yield pipe
        finally:
            pipe.execute()

    def init(self, iteration: Iteration) -> None:
        shardsets = [s for s in iteration.shardsets if len(s.shards) > 0]

        if len(shardsets) == 0:
            # never happens unless all shardsets have 0 samples
            raise IterationStateException(
                "Please add at least one shardset and one shard to the dataset",
            )

        main_shardset = get_main_shardset(shardsets)

        self._set_iteration_info(iteration)
        self._set_shardsets_info(shardsets)
        self._set_main_shardset_info(
            main_shardset, iteration.shuffle, iteration.shuffle_seed
        )

    def push_indices(self, rank: int) -> None:
        retrieved_shuffle_seed = self._get("shuffle_seed")
        shuffle = retrieved_shuffle_seed is not None
        shuffle_seed = int(retrieved_shuffle_seed) if shuffle else None
        block_size = int(self._get("shuffle_block_size")) if shuffle else 1

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

        replication_pg = self._get("replication_pg")
        if replication_pg is not None:
            replication_pg = json.loads(replication_pg)

        with self.pipeline() as pipe:
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

    def pop_index(self, rank: int) -> int:
        retrieved = self.cache.lpop(self._key(f"indices:{rank}"), 1)
        if retrieved is None:
            with self.cache.lock(f"iteration:{self.iteration_id}"):
                self.push_indices(rank)
            retrieved = self.cache.lpop(self._key(f"indices:{rank}"), 1)

        if retrieved is None:
            raise IterationStateException("No more indices to pop")

        index = int(retrieved[0])
        now = time.time()
        self.cache.hset(self._key("inprogress"), index, f"{rank}:{now}")

        return index

    def pushback_inprogress(self) -> None:
        for inprogress in self.get_inprogress():
            self.cache.lpush(self._key(f"indices:{inprogress.rank}"), inprogress.index)
        self.cache.delete(self._key("inprogress"))

    def complete(self, index: int) -> None:
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

    def get_shards_from_index(
        self, index: int
    ) -> tuple[MainShardInfo, list[ShardInfo]]:
        main_shardset_id = self._get("main_shardset").decode("utf-8")
        shard_samples = [
            int(s) for s in self._list_all(f"shardsets:{main_shardset_id}:samples")
        ]
        shard_index, sample_index = span(index, shard_samples)
        main_shard = MainShardInfo(
            sample_index=sample_index,
            **self._get_shard_info(main_shardset_id, shard_index).model_dump(),
        )

        shardsets = self._list_all("shardsets")
        shardsets = [s.decode("utf-8") for s in shardsets]
        shards: list[ShardInfo] = [
            self._get_shard_info(shardset_id, shard_index)
            for shardset_id in shardsets
            if shardset_id != main_shardset_id
        ]

        if main_shard is None:
            raise IterationStateException("Main shard not found")

        return main_shard, shards

    def get_batch_size(self) -> int:
        return int(self._get("batch_size"))

    def get_preprocessor(self) -> Optional[str]:
        v = self._get("preprocessor")
        if v is None:
            return None
        return v.decode("utf-8")

    def get_filter(self) -> Optional[str]:
        v = self._get("filter")
        if v is None:
            return None
        return v.decode("utf-8")

    def get_collater(self) -> Optional[str]:
        v = self._get("collater")
        if v is None:
            return None
        return v.decode("utf-8")

    def next_item(self, rank: int) -> GetSampleParams:
        pipe = self.cache.pipeline()
        pipe.get(self._key("uid_column_name"))
        pipe.get(self._key("uid_column_type"))
        [uid_column_name, uid_column_type] = pipe.execute()
        uid_column_name = uid_column_name.decode("utf-8")
        uid_column_type = uid_column_type.decode("utf-8")
        index = self.pop_index(rank)
        main_shard, feature_shards = self.get_shards_from_index(index)
        return GetSampleParams(
            index=index,
            uid_column_name=uid_column_name,
            uid_column_type=uid_column_type,
            main_shard=main_shard,
            feature_shards=feature_shards,
        )

    def get_inprogress(self) -> list[InProgressIndex]:
        return [
            InProgressIndex(
                index=int(k.decode("utf-8")),
                rank=int(v.decode("utf-8").split(":")[0]),
                started_at=float(v.decode("utf-8").split(":")[1]),
            )
            for k, v in self.cache.hgetall(self._key("inprogress")).items()
        ]

    def get_progress(self) -> Progress:
        pushed = self.cache.incr(self._key("pushed"), 0)
        inqueue = 0

        replication_pg = self._get("replication_pg")
        if replication_pg is not None:
            replication_pg = json.loads(replication_pg)

        if replication_pg is not None:
            pipe = self.cache.pipeline()
            for pg in replication_pg:
                pipe.llen(self._key(f"indices:{pg[0]}"))
            inqueue = sum(pipe.execute())
        else:
            ranks = [
                int(k.decode("utf-8").split("indices:", 1)[1])
                for k in self.cache.keys(self._key("indices:*"))
            ]
            pipe = self.cache.pipeline()
            for rank in ranks:
                pipe.llen(self._key(f"indices:{rank}"))
            inqueue = sum(pipe.execute())

        total = int(self._get("total"))
        current = pushed - inqueue
        inprogress = self.get_inprogress()
        completed = self.cache.incr(self._key("completed"), 0)
        filtered = self.cache.incr(self._key("filtered"), 0)
        failed = self.cache.incr(self._key("failed"), 0)

        return Progress(
            current=current,
            inprogress=inprogress,
            completed=completed,
            filtered=filtered,
            failed=failed,
            total=total,
        )
