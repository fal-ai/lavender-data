from typing import Optional, Any

from fastapi import HTTPException, APIRouter
from sqlmodel import select, update
from sqlalchemy.exc import NoResultFound, IntegrityError
from pydantic import BaseModel
from lavender_data.server.db import DbSession
from lavender_data.server.db.models import (
    Dataset,
    Shardset,
    Shard,
    DatasetColumn,
    DatasetPublic,
    ShardsetPublic,
    ShardPublic,
    DatasetColumnPublic,
)
from lavender_data.server.services.reader import (
    ReaderInstance,
    GetSampleParams,
    ShardInfo,
    MainShardInfo,
)
from lavender_data.server.services.iterations import get_main_shardset, span

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/")
def get_datasets(session: DbSession, name: Optional[str] = None) -> list[DatasetPublic]:
    query = select(Dataset).order_by(Dataset.created_at.desc())
    if name is not None:
        query = query.where(Dataset.name == name)
    return session.exec(query).all()


class GetDatasetResponse(DatasetPublic):
    columns: list[DatasetColumnPublic]
    shardsets: list[ShardsetPublic]


@router.get("/{dataset_id}")
def get_dataset(dataset_id: str, session: DbSession) -> GetDatasetResponse:
    try:
        dataset = session.get_one(Dataset, dataset_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


def read_dataset(
    dataset: Dataset, index: int, reader: ReaderInstance
) -> GetSampleParams:
    main_shardset = get_main_shardset(dataset.shardsets)
    shard_index, sample_index = span(
        index, [shard.samples for shard in main_shardset.shards]
    )

    uid_column_type = None
    feature_shards = []
    for shardset in dataset.shardsets:
        columns = {column.name: column.type for column in shardset.columns}
        if dataset.uid_column_name in columns:
            uid_column_type = columns[dataset.uid_column_name]

        shard = shardset.shards[shard_index]

        shard_info = ShardInfo(
            shardset_id=shardset.id,
            index=shard.index,
            samples=shard.samples,
            location=shard.location,
            format=shard.format,
            filesize=shard.filesize,
            columns=columns,
        )
        if shardset.id == main_shardset.id:
            main_shard = MainShardInfo(
                **shard_info.model_dump(), sample_index=sample_index
            )
        else:
            feature_shards.append(shard_info)

    if uid_column_type is None:
        raise HTTPException(status_code=400, detail="Dataset has no uid column")

    return reader.get_sample(
        GetSampleParams(
            index=0,
            uid_column_name=dataset.uid_column_name,
            uid_column_type=uid_column_type,
            main_shard=main_shard,
            feature_shards=feature_shards,
        )
    )


class PreviewDatasetResponse(BaseModel):
    dataset: DatasetPublic
    columns: list[DatasetColumnPublic]
    samples: list[dict[str, Any]]
    total: int


@router.get("/{dataset_id}/preview")
def preview_dataset(
    dataset_id: str,
    session: DbSession,
    reader: ReaderInstance,
    offset: int = 0,
    limit: int = 10,
) -> PreviewDatasetResponse:
    try:
        dataset = session.get_one(Dataset, dataset_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Dataset not found")

    samples = []
    for index in range(offset, offset + limit):
        try:
            sample = read_dataset(dataset, index, reader)
        except IndexError:
            break

        for key in sample.keys():
            if type(sample[key]) == bytes:
                sample[key] = "<bytes>"

        samples.append(sample)

    return PreviewDatasetResponse(
        dataset=dataset,
        columns=dataset.columns,
        samples=samples,
        total=get_main_shardset(dataset.shardsets).total_samples,
    )


class CreateDatasetParams(BaseModel):
    name: str
    uid_column_name: Optional[str] = None


@router.post("/")
def create_dataset(params: CreateDatasetParams, session: DbSession) -> DatasetPublic:
    dataset = Dataset(name=params.name, uid_column_name=params.uid_column_name)
    session.add(dataset)
    try:
        session.commit()
    except IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=409, detail="unique constraint failed")
        raise
    return dataset


class DatasetColumnOptions(BaseModel):
    name: str
    type: str
    description: Optional[str] = None


class CreateShardsetParams(BaseModel):
    location: str
    columns: list[DatasetColumnOptions]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "location": "s3://bucket/path/to/shardset/",
                    "columns": [
                        {
                            "name": "caption",
                            "type": "text",
                            "description": "A caption for the image",
                        },
                        {
                            "name": "image_url",
                            "type": "text",
                            "description": "An image",
                        },
                    ],
                }
            ]
        }
    }


class CreateShardsetResponse(ShardsetPublic):
    columns: list[DatasetColumnPublic]


@router.post("/{dataset_id}/shardsets")
def create_shardset(
    dataset_id: str, params: CreateShardsetParams, session: DbSession
) -> CreateShardsetResponse:
    try:
        dataset = session.get_one(Dataset, dataset_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Dataset not found")

    shardset = Shardset(dataset_id=dataset.id, location=params.location)
    session.add(shardset)

    if len(params.columns) == 0:
        raise HTTPException(status_code=400, detail="columns is required")

    if len(set(options.name for options in params.columns)) != len(params.columns):
        raise HTTPException(status_code=400, detail="column names must be unique")

    try:
        uid_column = session.exec(
            select(DatasetColumn).where(
                DatasetColumn.dataset_id == dataset.id,
                DatasetColumn.name == dataset.uid_column_name,
            )
        ).one()
    except NoResultFound:
        uid_column = None

    columns = [
        DatasetColumn(
            dataset_id=dataset.id,
            shardset_id=shardset.id,
            name=options.name,
            type=options.type,
            description=options.description,
        )
        for options in params.columns
        if uid_column is None or options.name != uid_column.name
    ]
    session.add_all(columns)

    try:
        session.commit()
    except IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=409, detail="unique constraint failed")
        raise

    session.refresh(shardset)
    return shardset


class CreateShardParams(BaseModel):
    location: str
    filesize: int
    samples: int
    format: str
    index: int

    overwrite: bool = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "location": "s3://bucket/path/to/shard/",
                    "filesize": 1024 * 1024 * 10,
                    "samples": 100,
                    "format": "parquet",
                    "index": 0,
                    "overwrite": True,
                },
            ]
        }
    }


class NextShardIndexResponse(BaseModel):
    shard_index: int


@router.post("/{dataset_id}/shardsets/{shardset_id}/shards")
def create_shard(
    dataset_id: str,
    shardset_id: str,
    params: CreateShardParams,
    session: DbSession,
) -> ShardPublic:
    try:
        shardset = session.exec(
            select(Shardset).where(
                Shardset.id == shardset_id,
                Shardset.dataset_id == dataset_id,
            )
        ).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Shardset not found")

    shardset.total_samples = Shardset.total_samples + params.samples
    shardset.shard_count = Shardset.shard_count + 1
    session.add(shardset)

    if params.overwrite:
        result = session.exec(
            update(Shard)
            .where(
                Shard.shardset_id == shardset.id,
                Shard.index == params.index,
            )
            .values(
                location=params.location,
                filesize=params.filesize,
                samples=params.samples,
                format=params.format,
            )
        )
        if result.rowcount > 0:
            return session.exec(
                select(Shard).where(
                    Shard.shardset_id == shardset.id,
                    Shard.index == params.index,
                )
            ).one()

    try:
        shard = Shard(
            shardset_id=shardset.id,
            location=params.location,
            filesize=params.filesize,
            samples=params.samples,
            index=params.index,
            format=params.format,
        )
        session.add(shard)
        session.commit()
        session.refresh(shard)
    except IntegrityError as e:
        if "unique_shardset_index" in str(e):
            if not params.overwrite:
                raise HTTPException(
                    status_code=409,
                    detail=f"shard index {params.index} for shardset {shardset_id} already exists. Set overwrite=True to overwrite the shard.",
                )

        raise
    return shard
