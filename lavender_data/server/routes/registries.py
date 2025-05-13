from fastapi import APIRouter

from lavender_data.server.registries import (
    FilterRegistry,
    CategorizerRegistry,
    CollaterRegistry,
    PreprocessorRegistry,
)

router = APIRouter(prefix="/registries", tags=["registries"])


@router.get("/filters")
def get_filters() -> list[str]:
    return FilterRegistry.list()


@router.get("/categorizers")
def get_categorizers() -> list[str]:
    return CategorizerRegistry.list()


@router.get("/collaters")
def get_collaters() -> list[str]:
    return CollaterRegistry.list()


@router.get("/preprocessors")
def get_preprocessors() -> list[str]:
    return PreprocessorRegistry.list()
