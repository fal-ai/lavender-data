import time
import random
import string
from typing import Optional, Any
from typing_extensions import TypedDict
from datetime import datetime
from sqlmodel import (
    Field,
    SQLModel,
    UniqueConstraint,
    Relationship,
    JSON,
)
from sqlalchemy import Column, DateTime, func
from numpy import base_repr


def generate_uid(prefix: str, length: int = 20):
    def generate_uid_inner():
        ts = base_repr(int(time.time() * 1000), 36).lower()
        rand = "".join(
            random.choice(string.ascii_lowercase + string.digits)
            for _ in range(length - len(ts))
        )
        return f"{prefix}-{ts}{rand}"

    return generate_uid_inner


def DateTimeField(*, nullable: bool = False, server_default=None):
    return Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=nullable,
            server_default=server_default,
        ),
    )


def CreatedAtField():
    return DateTimeField(nullable=False, server_default=func.now())


"""
Dataset
"""


class DatasetBase(SQLModel):
    id: str = Field(primary_key=True, default_factory=generate_uid("ds"))
    name: str = Field(unique=True)
    uid_column_name: str = Field(default="uid")
    created_at: datetime = CreatedAtField()


class Dataset(DatasetBase, table=True):
    columns: list["DatasetColumn"] = Relationship(back_populates="dataset")
    shardsets: list["Shardset"] = Relationship(back_populates="dataset")
    iterations: list["Iteration"] = Relationship(back_populates="dataset")


class DatasetPublic(DatasetBase):
    pass


class ShardsetBase(SQLModel):
    id: str = Field(primary_key=True, default_factory=generate_uid("ss"))
    dataset_id: str = Field(foreign_key="dataset.id")
    location: str = Field()
    shard_count: int = Field(default=0)
    total_samples: int = Field(default=0)
    created_at: datetime = CreatedAtField()


class Shardset(ShardsetBase, table=True):
    columns: list["DatasetColumn"] = Relationship(back_populates="shardset")
    dataset: "Dataset" = Relationship(back_populates="shardsets")
    shards: list["Shard"] = Relationship(back_populates="shardset")

    __table_args__ = (
        UniqueConstraint("dataset_id", "location", name="unique_dataset_location"),
    )


class ShardsetPublic(ShardsetBase):
    pass


class ShardBase(SQLModel):
    id: str = Field(primary_key=True, default_factory=generate_uid("sd"))
    shardset_id: str = Field(foreign_key="shardset.id")
    location: str = Field()
    filesize: int = Field(default=0)
    samples: int = Field(default=0)
    index: int = Field(default=0)
    format: str = Field()
    created_at: datetime = CreatedAtField()

    __table_args__ = (
        UniqueConstraint("shardset_id", "index", name="unique_shardset_index"),
    )


class Shard(ShardBase, table=True):
    shardset: "Shardset" = Relationship(back_populates="shards")


class ShardPublic(ShardBase):
    pass


class DatasetColumnBase(SQLModel):
    id: str = Field(primary_key=True, default_factory=generate_uid("dc"))
    dataset_id: str = Field(foreign_key="dataset.id")
    shardset_id: str = Field(foreign_key="shardset.id")
    name: str = Field()
    type: str = Field()
    description: Optional[str] = Field(default=None)
    created_at: datetime = CreatedAtField()


class DatasetColumn(DatasetColumnBase, table=True):
    dataset: "Dataset" = Relationship(back_populates="columns")
    shardset: "Shardset" = Relationship(back_populates="columns")

    __table_args__ = (
        UniqueConstraint("dataset_id", "name", name="unique_dataset_name"),
    )


class DatasetColumnPublic(DatasetColumnBase):
    pass


"""
Iteration
"""


class IterationShardsetLink(SQLModel, table=True):
    iteration_id: str = Field(primary_key=True, foreign_key="iteration.id")
    shardset_id: str = Field(primary_key=True, foreign_key="shardset.id")


class IterationFilter(TypedDict):
    name: str
    params: dict[str, Any]


class IterationPreprocessor(TypedDict):
    name: str
    params: dict[str, Any]


class IterationCollater(TypedDict):
    name: str
    params: dict[str, Any]


class IterationBase(SQLModel):
    id: str = Field(primary_key=True, default_factory=generate_uid("it"))
    dataset_id: str = Field(foreign_key="dataset.id")
    total: int = Field(default=0)

    filters: Optional[list[IterationFilter]] = Field(default=None, sa_type=JSON)
    preprocessors: Optional[list[IterationPreprocessor]] = Field(
        default=None, sa_type=JSON
    )
    collater: Optional[IterationCollater] = Field(default=None, sa_type=JSON)

    shuffle: bool = Field(default=False)
    shuffle_seed: Optional[int] = Field(default=None)
    shuffle_block_size: Optional[int] = Field(default=None)

    batch_size: int = Field(default=0)

    replication_pg: Optional[list[list[int]]] = Field(default=None, sa_type=JSON)

    created_at: datetime = CreatedAtField()


class Iteration(IterationBase, table=True):
    dataset: "Dataset" = Relationship(back_populates="iterations")
    shardsets: list["Shardset"] = Relationship(
        link_model=IterationShardsetLink,
    )


class IterationPublic(IterationBase):
    pass


"""
Auth
"""


class ApiKey(SQLModel, table=True):
    id: str = Field(primary_key=True, default_factory=generate_uid("la"))
    note: Optional[str] = Field(nullable=True)
    secret: str = Field()
    locked: bool = Field(default=False)
    created_at: datetime = CreatedAtField()
    expires_at: Optional[datetime] = DateTimeField(nullable=True)
    last_accessed_at: Optional[datetime] = DateTimeField(nullable=True)
