import os
import json
from typing import Optional, Any
from concurrent.futures import Future

from fastapi import HTTPException, APIRouter, Depends
from sqlmodel import select, delete
from sqlalchemy.exc import NoResultFound, IntegrityError
from pydantic import BaseModel

from lavender_data.logging import get_logger
from lavender_data.server.db import DbSession
from lavender_data.server.db.models import (
    Dataset,
    Shardset,
    Shard,
    DatasetColumn,
    IterationShardsetLink,
    DatasetPublic,
    ShardsetPublic,
    ShardPublic,
    DatasetColumnPublic,
    Iteration,
    IterationPreprocessor,
)
from lavender_data.server.cache import CacheClient
from lavender_data.server.distributed import CurrentCluster
from lavender_data.server.reader import (
    ReaderInstance,
    GlobalSampleIndex,
    ShardInfo,
    MainShardInfo,
)
from lavender_data.server.background_worker import CurrentBackgroundWorker, TaskStatus
from lavender_data.server.shardset import (
    get_main_shardset,
    span,
    sync_shardset_location_task,
    preprocess_dataset_task,
)
from lavender_data.server.auth import AppAuth
from lavender_data.storage import list_files
from lavender_data.shard import inspect_shard

router = APIRouter(
    prefix="/datasets",
    tags=["datasets"],
    dependencies=[Depends(AppAuth(api_key_auth=True, cluster_auth=True))],
)


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
) -> GlobalSampleIndex:
    main_shardset = get_main_shardset(dataset.shardsets)
    shard_index, sample_index = span(
        index,
        [
            shard.samples
            for shard in sorted(main_shardset.shards, key=lambda s: s.index)
        ],
    )

    main_shard = None
    uid_column_type = None
    feature_shards = []
    for shardset in dataset.shardsets:
        columns = {column.name: column.type for column in shardset.columns}
        if dataset.uid_column_name in columns:
            uid_column_type = columns[dataset.uid_column_name]

        try:
            shard = [
                shard
                for shard in sorted(shardset.shards, key=lambda s: s.index)
                if shard.index == shard_index
            ][0]
        except IndexError:
            # f"Shard index {shard_index} not found in shardset {shardset.id}",
            continue

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

    if main_shard is None:
        raise HTTPException(status_code=400, detail="Dataset has no shards")

    return reader.get_sample(
        GlobalSampleIndex(
            index=index,
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

    if len(dataset.shardsets) == 0:
        raise HTTPException(status_code=400, detail="Dataset has no shardsets")

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
def create_dataset(
    params: CreateDatasetParams,
    session: DbSession,
    cluster: CurrentCluster,
) -> DatasetPublic:
    dataset = Dataset(name=params.name, uid_column_name=params.uid_column_name)
    session.add(dataset)
    try:
        session.commit()
    except IntegrityError as e:
        if "unique constraint" in str(e) and "name" in str(e):
            raise HTTPException(status_code=409, detail="Dataset name must be unique")
        raise

    session.refresh(dataset)

    if cluster:
        cluster.sync_changes([dataset])

    return dataset


@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: str,
    session: DbSession,
    cluster: CurrentCluster,
) -> DatasetPublic:
    try:
        dataset = session.get_one(Dataset, dataset_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # TODO lock
    try:
        columns_to_delete = dataset.columns
        shardsets_to_delete = dataset.shardsets
        iterations_to_delete = dataset.iterations
        links_to_delete = session.exec(
            select(IterationShardsetLink).where(
                IterationShardsetLink.shardset_id.in_(
                    [s.id for s in shardsets_to_delete]
                ),
                IterationShardsetLink.iteration_id.in_(
                    [i.id for i in iterations_to_delete]
                ),
            )
        ).all()
        shards_to_delete = [
            shard for shardset in shardsets_to_delete for shard in shardset.shards
        ]
        if len(columns_to_delete) > 0:
            session.exec(
                delete(DatasetColumn).where(
                    DatasetColumn.id.in_([c.id for c in columns_to_delete])
                )
            )
        if len(links_to_delete) > 0:
            session.exec(
                delete(IterationShardsetLink).where(
                    IterationShardsetLink.id.in_([l.id for l in links_to_delete])
                )
            )
        if len(shards_to_delete) > 0:
            session.exec(
                delete(Shard).where(Shard.id.in_([s.id for s in shards_to_delete]))
            )
        if len(iterations_to_delete) > 0:
            session.exec(
                delete(Iteration).where(
                    Iteration.id.in_([i.id for i in iterations_to_delete])
                )
            )
        if len(shardsets_to_delete) > 0:
            session.exec(
                delete(Shardset).where(
                    Shardset.id.in_([s.id for s in shardsets_to_delete])
                )
            )
        session.exec(delete(Dataset).where(Dataset.id == dataset.id))
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

    if cluster:
        cluster.sync_changes(
            [
                dataset,
                *columns_to_delete,
                *links_to_delete,
                *iterations_to_delete,
                *shards_to_delete,
                *shardsets_to_delete,
            ],
            delete=True,
        )

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
    dataset_id: str,
    params: CreateShardsetParams,
    session: DbSession,
    background_worker: CurrentBackgroundWorker,
    cluster: CurrentCluster,
) -> CreateShardsetResponse:
    logger = get_logger(__name__)

    try:
        dataset = session.get_one(Dataset, dataset_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Dataset not found")

    shardset = Shardset(dataset_id=dataset.id, location=params.location)
    session.add(shardset)

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

    try:
        shard_basenames = sorted(list_files(params.location, limit=1))
    except Exception as e:
        shard_basenames = []
        logger.warning(f"Failed to list shardset location: {e}")

    if len(params.columns) == 0:
        if len(shard_basenames) == 0:
            raise HTTPException(
                status_code=400,
                detail="No shards found in location. Please either specify columns or provide a valid location with at least one shard.",
            )

        shard_basename = shard_basenames[0]
        try:
            shard_info = inspect_shard(os.path.join(params.location, shard_basename))
        except Exception as e:
            logger.exception(f"Failed to inspect shard: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to inspect shard")

        _columns = [
            DatasetColumnOptions(name=column_name, type=column_type)
            for column_name, column_type in shard_info.columns.items()
        ]
    else:
        _columns = params.columns

    columns = [
        DatasetColumn(
            dataset_id=dataset.id,
            shardset_id=shardset.id,
            name=column.name,
            type=column.type,
            description=column.description,
        )
        for column in _columns
        if (uid_column is None or column.name != uid_column.name)
        and column.name not in [c.name for c in dataset.columns]
    ]
    session.add_all(columns)

    try:
        session.commit()
    except IntegrityError as e:
        if "unique constraint" in str(e):
            raise HTTPException(status_code=409, detail="unique constraint failed")
        raise

    for column in columns:
        session.refresh(column)
    session.refresh(shardset)

    if cluster:
        cluster.sync_changes([shardset, *columns])

    if len(shard_basenames) > 0:
        sync_shardset(
            dataset_id=dataset_id,
            shardset_id=shardset.id,
            params=SyncShardsetParams(overwrite=True),
            session=session,
            background_worker=background_worker,
            cluster=cluster,
        )

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


class GetShardsetResponse(ShardsetPublic):
    shards: list[ShardPublic]
    columns: list[DatasetColumnPublic]


@router.get("/{dataset_id}/shardsets/{shardset_id}")
def get_shardset(
    dataset_id: str,
    shardset_id: str,
    session: DbSession,
) -> GetShardsetResponse:
    try:
        shardset = session.exec(
            select(Shardset).where(
                Shardset.id == shardset_id,
                Shardset.dataset_id == dataset_id,
            )
        ).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Shardset not found")

    return shardset


class SyncShardsetParams(BaseModel):
    overwrite: bool = False


def _sync_shardset_status_key(shardset_id: str) -> str:
    return f"sync-{shardset_id}"


def _sync_shardset_callback(cluster: CurrentCluster):
    def callback(future: Future):
        shardset: Shardset
        shards: list[Shard]
        shardset, shards = future
        logger = get_logger(__name__)
        if cluster is not None and cluster.is_head:
            try:
                logger.debug(
                    f"Syncing shardset {shardset.id} to cluster nodes ({len(shards)} shards)"
                )
                cluster.sync_changes([shardset, *shards])
            except Exception as e:
                logger.exception(e)

    return callback


@router.post("/{dataset_id}/shardsets/{shardset_id}/sync")
def sync_shardset(
    dataset_id: str,
    shardset_id: str,
    params: SyncShardsetParams,
    session: DbSession,
    background_worker: CurrentBackgroundWorker,
    cluster: CurrentCluster,
) -> GetShardsetResponse:
    try:
        shardset = session.exec(
            select(Shardset).where(
                Shardset.id == shardset_id,
                Shardset.dataset_id == dataset_id,
            )
        ).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Shardset not found")

    task_uid = _sync_shardset_status_key(shardset.id)

    existing = background_worker.memory().get_task_status(task_uid)
    if existing and existing.status != "done":
        raise HTTPException(
            status_code=400,
            detail="Shardset is already being synced. Please wait for the sync to complete.",
        )

    background_worker.submit(
        sync_shardset_location_task,
        on_complete=_sync_shardset_callback(cluster),
        shardset_id=shardset.id,
        shardset_location=shardset.location,
        shardset_shard_samples=[s.samples for s in shardset.shards],
        shardset_shard_locations=[s.location for s in shardset.shards],
        num_workers=10,
        overwrite=params.overwrite,
        task_uid=task_uid,
    )
    return shardset


@router.get("/{dataset_id}/shardsets/{shardset_id}/sync")
def get_sync_status(
    dataset_id: str,
    shardset_id: str,
    background_worker: CurrentBackgroundWorker,
) -> Optional[TaskStatus]:
    task_uid = _sync_shardset_status_key(shardset_id)
    status = background_worker.memory().get_task_status(task_uid)
    return status


def _shardset_lock_key(shardset_id: str) -> str:
    return f"shardset:{shardset_id}:lock"


@router.delete("/{dataset_id}/shardsets/{shardset_id}")
def delete_shardset(
    dataset_id: str,
    shardset_id: str,
    session: DbSession,
    cache: CacheClient,
    cluster: CurrentCluster,
) -> ShardsetPublic:
    try:
        shardset = session.exec(
            select(Shardset).where(
                Shardset.id == shardset_id,
                Shardset.dataset_id == dataset_id,
            )
        ).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Shardset not found")

    with cache.lock(_shardset_lock_key(shardset.id)):
        try:
            columns_to_delete = [
                column
                for column in shardset.columns
                if column.name != shardset.dataset.uid_column_name
                or len(shardset.dataset.shardsets) == 1
            ]
            links_to_delete = session.exec(
                select(IterationShardsetLink).where(
                    IterationShardsetLink.shardset_id == shardset.id
                )
            ).all()
            shards_to_delete = shardset.shards
            if len(columns_to_delete) > 0:
                session.exec(
                    delete(DatasetColumn).where(
                        DatasetColumn.id.in_([c.id for c in columns_to_delete])
                    )
                )
            if len(links_to_delete) > 0:
                session.exec(
                    delete(IterationShardsetLink).where(
                        IterationShardsetLink.shardset_id == shardset.id
                    )
                )
            if len(shards_to_delete) > 0:
                session.exec(
                    delete(Shard).where(Shard.shardset_id == shardset.id).returning()
                )
            session.exec(delete(Shardset).where(Shardset.id == shardset.id))
            session.commit()
        except Exception as e:
            session.rollback()
            raise e

        if cluster:
            cluster.sync_changes(
                [shardset, *columns_to_delete, *links_to_delete, *shards_to_delete],
                delete=True,
            )

    return shardset


class PreprocessDatasetParams(BaseModel):
    shardset_location: str
    source_shardset_ids: Optional[list[str]] = None
    preprocessors: list[IterationPreprocessor]
    export_columns: list[str]
    batch_size: int
    overwrite: bool = False


class PreprocessDatasetResponse(BaseModel):
    task_uid: str


@router.post("/{dataset_id}/preprocess")
def preprocess_dataset(
    dataset_id: str,
    params: PreprocessDatasetParams,
    session: DbSession,
    background_worker: CurrentBackgroundWorker,
) -> PreprocessDatasetResponse:
    if params.batch_size <= 0:
        raise HTTPException(status_code=400, detail="Batch size must be greater than 0")

    try:
        dataset = session.get_one(Dataset, dataset_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Dataset not found")

    uid_column = next(
        (c for c in dataset.columns if c.name == dataset.uid_column_name), None
    )
    if uid_column is None:
        raise HTTPException(status_code=400, detail="Dataset has no uid column")

    shardset_location = params.shardset_location
    preprocessors = params.preprocessors
    source_shardset_ids = params.source_shardset_ids or [
        s.id for s in dataset.shardsets
    ]

    task_uid = f'{dataset.id}-{"-".join([p["name"] for p in preprocessors])}-{shardset_location}'
    background_worker.submit(
        preprocess_dataset_task,
        shardset_location=shardset_location,
        source_shardset_ids=source_shardset_ids,
        uid_column_name=uid_column.name,
        uid_column_type=uid_column.type,
        preprocessors=preprocessors,
        export_columns=params.export_columns,
        batch_size=params.batch_size,
        overwrite=params.overwrite,
        task_uid=task_uid,
    )
    return PreprocessDatasetResponse(task_uid=task_uid)
