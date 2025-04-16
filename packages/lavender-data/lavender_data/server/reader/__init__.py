import os
from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel

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


class ServerSideReader:
    dirname: str = ".cache"
    reader_cache: dict[str, Reader] = {}

    def __init__(self, disk_cache_size: int):
        self.disk_cache_size = disk_cache_size

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

    def _ensure_cache_size(self):
        all_files = [
            os.path.join(r, file)
            for r, d, files in os.walk(self.dirname)
            for file in files
        ]
        while (
            sum([os.path.getsize(file) for file in all_files]) >= self.disk_cache_size
        ):
            oldest_file = min(all_files, key=os.path.getctime)
            os.remove(oldest_file)
            all_files.remove(oldest_file)

    def get_reader(self, shard: ShardInfo, uid_column_name: str, uid_column_type: str):
        cache_key = f"{shard.shardset_id}-{shard.index}"
        if cache_key not in self.reader_cache:
            self.reader_cache[cache_key] = self._get_reader(
                shard, uid_column_name, uid_column_type
            )
            self._ensure_cache_size()

        return self.reader_cache[cache_key]

    def get_sample(self, index: GlobalSampleIndex):
        reader = self.get_reader(
            index.main_shard, index.uid_column_name, index.uid_column_type
        )
        try:
            sample = reader.get_item_by_index(index.main_shard.sample_index)
        except IndexError:
            raise IndexError(
                f"Failed to read sample {index.main_shard.sample_index} from shard {index.main_shard.location} (shardset {index.main_shard.shardset_id}, {index.main_shard.samples} samples)"
            )
        sample_uid = sample[index.uid_column_name]

        for feature_shard in index.feature_shards:
            reader = self.get_reader(
                feature_shard, index.uid_column_name, index.uid_column_type
            )
            try:
                columns = reader.get_item_by_uid(sample_uid)
            except KeyError:
                raise KeyError(
                    f'Failed to read sample with uid "{sample_uid}" from shard {feature_shard.location} ({index.main_shard.sample_index} of {index.main_shard.location}) '
                )
            sample.update(columns)

        return sample


reader = None


def setup_reader(disk_cache_size: int):
    global reader
    reader = ServerSideReader(disk_cache_size=disk_cache_size)


def get_reader_instance():
    if not reader:
        raise RuntimeError("Reader not initialized")

    return reader


ReaderInstance = Annotated[ServerSideReader, Depends(get_reader_instance)]
