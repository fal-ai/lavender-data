import contextlib
import time
import numpy as np
import ujson as json
from typing import Optional

from fastapi import HTTPException


from lavender_data.logging import get_logger
from lavender_data.server.cache import CacheClient
from lavender_data.server.db.models import (
    Shardset,
    Iteration,
    IterationPreprocessor,
    IterationFilter,
    IterationCollater,
    IterationCategorizer,
)
from lavender_data.server.reader import (
    get_reader_instance,
    ShardInfo,
    MainShardInfo,
    GlobalSampleIndex,
    InnerJoinSampleInsufficient,
)
from lavender_data.server.registries import (
    FilterRegistry,
    CategorizerRegistry,
)
from lavender_data.server.shardset import get_main_shardset, span
from lavender_data.server.iteration.process import ProcessNextSamplesParams
from lavender_data.server.iteration.hash import _hash, get_iteration_hash
from lavender_data.serialize import serialize_sample, deserialize_sample

from .abc import IterationStateOps, Progress, InProgressIndex, IterationStateException


@contextlib.contextmanager
def np_seed(seed: int):
    state = np.random.get_state()
    np.random.seed(seed)
    try:
        yield
    finally:
        np.random.set_state(state)


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

            if iteration.filters is not None:
                pipe.set(self._key("filters"), json.dumps(iteration.filters))

            if iteration.categorizer is not None:
                pipe.set(self._key("categorizer"), json.dumps(iteration.categorizer))

            if iteration.collater is not None:
                pipe.set(self._key("collater"), json.dumps(iteration.collater))

            if iteration.preprocessors is not None:
                pipe.set(
                    self._key("preprocessors"), json.dumps(iteration.preprocessors)
                )

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

    def _categorizer(self) -> Optional[IterationCategorizer]:
        v = self.cache.get(self._key("categorizer"))
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
        if samples is None:
            raise IterationStateException(
                f"Shard {shard_index} of shardset {shardset_id} not found"
            )
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
        shards: list[ShardInfo] = []
        for shardset_id in shardsets:
            if shardset_id == main_shardset_id:
                continue
            try:
                shards.append(self._get_shard_info(shardset_id, shard_index))
            except IterationStateException:
                pass
            except Exception as e:
                # TODO handle error
                pass

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
        categorizer = self._categorizer()

        current = int(self.cache.incr(self._key(f"batch_count:{rank}"), 1)) - 1
        global_sample_indices = []
        samples = []
        while len(samples) < max(batch_size, 1):
            next_item = self.next_item(rank)

            try:
                sample = reader.get_sample(next_item, join="inner")
            except InnerJoinSampleInsufficient:
                self.filtered(next_item.index)
                continue
            except Exception as e:
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

            if categorizer is not None:
                bucket = CategorizerRegistry.get(categorizer["name"]).categorize(
                    sample, **categorizer["params"]
                )
                if not isinstance(bucket, str):
                    msg = f"Categorizer {categorizer['name']} returned {type(bucket)} instead of str"
                    logger.error(msg)
                    raise HTTPException(status_code=400, detail=msg)

                bucket_key = self._key(f"buckets:{bucket}")
                bucket_samples_key = self._key(f"bucket-samples:{bucket}")
                bucket_size = self.cache.llen(bucket_key)
                if bucket_size >= batch_size:
                    global_sample_indices.extend(
                        [
                            GlobalSampleIndex(**json.loads(i))
                            for i in self.cache.lpop(bucket_key, batch_size)
                        ]
                    )
                    samples.extend(
                        [
                            deserialize_sample(s)
                            for s in self.cache.lpop(bucket_samples_key, batch_size)
                        ]
                    )
                else:
                    self.cache.rpush(bucket_key, next_item.model_dump_json())
                    self.cache.rpush(bucket_samples_key, serialize_sample(sample))
            else:
                global_sample_indices.append(next_item)
                samples.append(sample)

        cache_key = self._cache_key([i.index for i in global_sample_indices])
        return cache_key, ProcessNextSamplesParams(
            current=current,
            global_sample_indices=global_sample_indices,
            samples=samples,
            collater=self._collater(),
            preprocessors=self._preprocessors(),
            batch_size=self._batch_size(),
        )
