from fastapi import APIRouter

from lavender_data.server.services.registries import (
    PreprocessorRegistry,
    FilterRegistry,
    CollaterRegistry,
)

router = APIRouter(prefix="/registries", tags=["registries"])


@router.get("/preprocessors")
def get_preprocessors() -> list[str]:
    return PreprocessorRegistry.list()


@router.get("/filters")
def get_filters() -> list[str]:
    return FilterRegistry.list()


@router.get("/collaters")
def get_collaters() -> list[str]:
    return CollaterRegistry.list()
