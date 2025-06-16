import filetype
import json
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from lavender_data.server.db import DbSession
from lavender_data.server.reader import ReaderInstance
from lavender_data.server.auth import AppAuth
from lavender_data.server.reader import get_reader_instance
from lavender_data.server.background_worker import (
    get_shared_memory,
    CurrentBackgroundWorker,
    CurrentSharedMemory,
)

router = APIRouter(
    prefix="/files",
    tags=["files"],
    dependencies=[Depends(AppAuth(api_key_auth=True, cluster_auth=True))],
)


class FileType(BaseModel):
    video: bool
    image: bool


def _get_file_type(file_path: str) -> FileType:
    kind = filetype.guess(file_path)
    if kind is None:
        return FileType(video=False, image=False)
    return FileType(
        video=kind.mime.startswith("video/"),
        image=kind.mime.startswith("image/"),
    )


def _get_file(file_url: str):
    reader = get_reader_instance()
    memory = get_shared_memory()
    f = reader.get_file(file_url)
    file_type = _get_file_type(f)

    memory.set(f"file_type:{file_url}", file_type.model_dump_json(), ex=3 * 60)
    return file_type


class InspectFileTypeParams(BaseModel):
    file_url: str


@router.post("/type")
def inspect_file_type(
    params: InspectFileTypeParams,
    background_worker: CurrentBackgroundWorker,
) -> dict:
    background_worker.submit(
        _get_file,
        file_url=params.file_url,
        task_id=params.file_url,
    )
    return {}


@router.get("/type")
def get_file_type(
    file_url: str,
    response: Response,
    memory: CurrentSharedMemory,
) -> FileType:
    file_type = memory.get(f"file_type:{file_url}")
    if file_type is None:
        raise HTTPException(status_code=400, detail="File not found")

    response.headers["Cache-Control"] = "public, max-age=3600"
    return FileType(**json.loads(file_type))


@router.get("/")
def get_file(session: DbSession, file_url: str, reader: ReaderInstance) -> FileResponse:
    try:
        f = reader.get_file(file_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid file URL")

    file_type = _get_file_type(f)
    if not file_type.image and not file_type.video:
        raise HTTPException(status_code=400, detail="Invalid file type")

    return FileResponse(f, headers={"Cache-Control": "public, max-age=3600"})
