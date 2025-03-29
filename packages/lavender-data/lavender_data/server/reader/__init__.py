import os
from typing import Annotated, Optional

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


class GetSampleParams(BaseModel):
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

    def _get_reader(self, shard: ShardInfo, uid_column_name: str, uid_column_type: str):
        shardset_dirname = os.path.join(
            self.dirname,
            shard.shardset_id,
        )

        if not os.path.exists(shardset_dirname):
            os.makedirs(shardset_dirname, exist_ok=True)
        elif not os.path.isdir(shardset_dirname):
            raise ValueError(f"Failed to create directory {shardset_dirname}")
        elif len(os.listdir(shardset_dirname)) >= self.disk_cache_size:
            oldest_file = min(os.listdir(shardset_dirname), key=os.path.getctime)
            os.remove(os.path.join(shardset_dirname, oldest_file))

        dirname = os.path.join(
            shardset_dirname,
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
            dirname=dirname,
            uid_column_name=uid_column_name,
            uid_column_type=uid_column_type,
        )

    def get_reader(self, shard: ShardInfo, uid_column_name: str, uid_column_type: str):
        cache_key = f"{shard.shardset_id}-{shard.index}"
        if cache_key not in self.reader_cache:
            self.reader_cache[cache_key] = self._get_reader(
                shard, uid_column_name, uid_column_type
            )

        return self.reader_cache[cache_key]

    def get_sample(self, params: GetSampleParams):
        reader = self.get_reader(
            params.main_shard, params.uid_column_name, params.uid_column_type
        )
        try:
            sample = reader.get_item_by_index(params.main_shard.sample_index)
        except IndexError:
            raise IndexError(
                f"Failed to read sample {params.main_shard.sample_index} from shard {params.main_shard.location} (shardset {params.main_shard.shardset_id}, {params.main_shard.samples} samples)"
            )
        sample_uid = sample[params.uid_column_name]

        for feature_shard in params.feature_shards:
            reader = self.get_reader(
                feature_shard, params.uid_column_name, params.uid_column_type
            )
            try:
                columns = reader.get_item_by_uid(sample_uid)
            except KeyError:
                raise KeyError(
                    f'Failed to read sample with uid "{sample_uid}" from shard {feature_shard.location} ({params.main_shard.sample_index} of {params.main_shard.location}) '
                )
            sample.update(columns)

        return sample


reader = None


def setup_reader(disk_cache_size: Optional[int] = None):
    global reader
    reader = ServerSideReader(disk_cache_size=disk_cache_size or 100)


def get_reader_instance():
    if not reader:
        raise RuntimeError("Reader not initialized")

    return reader


ReaderInstance = Annotated[ServerSideReader, Depends(get_reader_instance)]
