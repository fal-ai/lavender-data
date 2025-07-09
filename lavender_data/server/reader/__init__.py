import os
import hashlib
from typing import Annotated, Optional, Literal

import numpy as np
from fastapi import Depends
from pydantic import BaseModel

from lavender_data.server.settings import root_dir
from lavender_data.shard import Reader


class ShardInfo(BaseModel):
    shardset_id: str
    index: int
    samples: int
    location: str
    format: str
    filesize: int
    columns: dict[str, str]


class MainShardInfo(ShardInfo):
    sample_index: int


class GlobalSampleIndex(BaseModel):
    index: int
    uid_column_name: str
    uid_column_type: str
    main_shard: MainShardInfo
    feature_shards: list[ShardInfo]


def _default_null_type(t: str) -> str:
    if t.startswith("int"):
        return np.nan
    elif t.startswith("float") or t.startswith("double"):
        return np.nan
    elif t.startswith("text") or t.startswith("str"):
        return ""
    elif t.startswith("binary"):
        return b""
    elif t.startswith("bool"):
        return np.nan
    elif t.startswith("list"):
        return []
    elif t.startswith("dict"):
        return {}
    else:
        return None


JoinMethod = Literal["inner", "left"]


class InnerJoinSampleInsufficient(Exception):
    pass


class ServerSideReader:
    reader_cache: dict[str, Reader] = {}

    def __init__(self, disk_cache_size: int, dirname: Optional[str] = None):
        self.disk_cache_size = disk_cache_size
        if dirname is None:
            self.dirname = os.path.join(root_dir, ".cache")
        else:
            self.dirname = dirname

        if not os.path.exists(self.dirname):
            os.makedirs(self.dirname, exist_ok=True)
        elif not os.path.isdir(self.dirname):
            raise ValueError(f"Failed to create cache directory {self.dirname}")

    def _get_reader(self, shard: ShardInfo, uid_column_name: str, uid_column_type: str):
        filepath = None
        dirname = None

        if shard.location.startswith("file://"):
            # no need to copy/download
            filepath = shard.location.replace("file://", "")
        else:
            # download
            dirname = os.path.join(
                self.dirname,
                os.path.dirname(shard.location.replace("://", "/")),
            )

            if not os.path.exists(dirname):
                os.makedirs(dirname, exist_ok=True)
            elif not os.path.isdir(dirname):
                raise ValueError(f"Failed to create directory {dirname}")

        return Reader.get(
            format=shard.format,
            location=shard.location,
            columns=shard.columns,
            filepath=filepath,
            dirname=dirname,
            uid_column_name=uid_column_name,
            uid_column_type=uid_column_type,
        )

    def _get_cache_files(self):
        return [
            os.path.join(r, file)
            for r, d, files in os.walk(self.dirname)
            for file in files
        ]

    def _get_cache_size(self):
        all_filesize = 0
        for file in self._get_cache_files():
            try:
                # deleted during the loop
                all_filesize += os.path.getsize(file)
            except FileNotFoundError:
                continue

        return all_filesize

    def _get_oldest_cache_file(self):
        return min(self._get_cache_files(), key=os.path.getctime)

    def _ensure_cache_size(self):
        while self._get_cache_size() >= self.disk_cache_size:
            oldest_file = self._get_oldest_cache_file()
            os.remove(oldest_file)

    def _get_reader_cache_key(self, shard: ShardInfo):
        return hashlib.md5(
            str(
                (
                    shard.shardset_id,
                    shard.location,
                    shard.samples,
                    shard.format,
                    shard.filesize,
                )
            ).encode()
        ).hexdigest()

    def get_reader(
        self, shard: ShardInfo, uid_column_name: str, uid_column_type: str
    ) -> Reader:
        cache_key = self._get_reader_cache_key(shard)
        if cache_key not in self.reader_cache:
            self.reader_cache[cache_key] = self._get_reader(
                shard, uid_column_name, uid_column_type
            )
            self._ensure_cache_size()

        return self.reader_cache[cache_key]

    def clear_cache(self, *shards: list[ShardInfo]):
        for shard in shards:
            cache_key = self._get_reader_cache_key(shard)
            if cache_key in self.reader_cache:
                self.reader_cache[cache_key].clear()
                del self.reader_cache[cache_key]

    def _get_sample(
        self,
        index: GlobalSampleIndex,
        join: JoinMethod,
    ):
        reader = self.get_reader(
            index.main_shard, index.uid_column_name, index.uid_column_type
        )
        try:
            sample = reader.get_item_by_index(index.main_shard.sample_index)
        except IndexError:
            raise IndexError(
                f"Failed to read sample {index.main_shard.sample_index} from shard {index.main_shard.location} (shardset {index.main_shard.shardset_id}, {index.main_shard.samples} samples)"
            )

        try:
            sample_uid = sample[index.uid_column_name]
        except KeyError:
            raise KeyError(
                f"Sample does not have uid column {index.uid_column_name} (available columns: {','.join(sample.keys())}) "
                f"in shard {index.main_shard.location} (shardset {index.main_shard.shardset_id}, {index.main_shard.samples} samples)"
            )

        for feature_shard in index.feature_shards:
            reader = self.get_reader(
                feature_shard, index.uid_column_name, index.uid_column_type
            )
            try:
                sample_partial = reader.get_item_by_uid(sample_uid)
            except KeyError:
                if join == "inner":
                    raise InnerJoinSampleInsufficient(
                        f'Failed to read sample with uid "{sample_uid}" from shard {feature_shard.location} ({index.main_shard.sample_index} of {index.main_shard.location})'
                    )
                else:
                    sample_partial = {
                        k: _default_null_type(t)
                        for k, t in feature_shard.columns.items()
                    }
            for k, v in sample_partial.items():
                if k == index.uid_column_name:
                    continue
                if v is None:
                    sample[k] = _default_null_type(feature_shard.columns[k])
                    continue
                sample[k] = v

        return sample

    def get_sample(
        self,
        index: GlobalSampleIndex,
        join: JoinMethod = "inner",
    ):
        try:
            return self._get_sample(index, join)
        except InnerJoinSampleInsufficient:
            raise
        except Exception as e:
            self.clear_cache(index.main_shard, *index.feature_shards)
            raise e


reader = None


def setup_reader(disk_cache_size: int):
    global reader
    reader = ServerSideReader(disk_cache_size=disk_cache_size)


def get_reader_instance():
    if not reader:
        raise RuntimeError("Reader not initialized")

    return reader


ReaderInstance = Annotated[ServerSideReader, Depends(get_reader_instance)]
