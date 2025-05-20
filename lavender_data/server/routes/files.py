import filetype
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from lavender_data.server.db import DbSession
from lavender_data.server.reader import ReaderInstance
from lavender_data.server.auth import AppAuth

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


@router.get("/type")
def get_file_type(
    session: DbSession, file_url: str, reader: ReaderInstance, response: Response
) -> FileType:
    try:
        f = reader.get_file(file_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid file URL")

    response.headers["Cache-Control"] = "public, max-age=3600"
    return _get_file_type(f)


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
