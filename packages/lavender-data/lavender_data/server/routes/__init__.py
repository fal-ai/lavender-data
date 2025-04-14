from fastapi import APIRouter
from pydantic import BaseModel
import importlib.metadata

from .datasets import router as datasets_router
from .iterations import router as iterations_router
from .registries import router as registries_router

__all__ = [
    "root_router",
    "datasets_router",
    "iterations_router",
    "registries_router",
]

root_router = APIRouter(prefix="", tags=["root"])


class VersionResponse(BaseModel):
    version: str


@root_router.get("/version", response_model=VersionResponse)
def version():
    version = importlib.metadata.version("lavender-data")
    return {"version": version}
