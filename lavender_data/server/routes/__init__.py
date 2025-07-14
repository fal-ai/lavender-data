from fastapi import APIRouter
from pydantic import BaseModel
import importlib.metadata

from .datasets import router as datasets_router
from .iterations import router as iterations_router
from .registries import router as registries_router
from .cluster import router as cluster_router
from .background_tasks import router as background_tasks_router

__all__ = [
    "root_router",
    "datasets_router",
    "iterations_router",
    "registries_router",
    "cluster_router",
    "background_tasks_router",
]

root_router = APIRouter(prefix="", tags=["root"])


class VersionResponse(BaseModel):
    version: str


@root_router.get("/version", response_model=VersionResponse)
def version():
    try:
        version = importlib.metadata.version("lavender-data")
    except importlib.metadata.PackageNotFoundError:
        version = "dev"
    return {"version": version}
