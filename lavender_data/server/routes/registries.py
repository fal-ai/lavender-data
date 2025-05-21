from fastapi import APIRouter

from lavender_data.server.registries import (
    FuncSpec,
    FilterRegistry,
    CategorizerRegistry,
    CollaterRegistry,
    PreprocessorRegistry,
)

router = APIRouter(prefix="/registries", tags=["registries"])


@router.get("/filters")
def get_filters() -> list[FuncSpec]:
    return FilterRegistry.specs()


@router.get("/categorizers")
def get_categorizers() -> list[FuncSpec]:
    return CategorizerRegistry.specs()


@router.get("/collaters")
def get_collaters() -> list[FuncSpec]:
    return CollaterRegistry.specs()


@router.get("/preprocessors")
def get_preprocessors() -> list[FuncSpec]:
    return PreprocessorRegistry.specs()
