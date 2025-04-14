import re
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lavender_data.logging import get_logger

from .db import setup_db, create_db_and_tables
from .cache import setup_cache, register_worker, deregister_worker
from .reader import setup_reader
from .routes import (
    datasets_router,
    iterations_router,
    registries_router,
    root_router,
)

from .services.registries import import_from_directory
from .settings import get_settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    setup_db(settings.lavender_data_db_url)
    create_db_and_tables()

    setup_cache(redis_url=settings.lavender_data_redis_url)

    if settings.lavender_data_modules_dir:
        import_from_directory(settings.lavender_data_modules_dir)

    setup_reader(int(settings.lavender_data_reader_disk_cache_size))

    rank = register_worker()
    app.state.rank = rank

    if settings.lavender_data_disable_auth:
        logger.warning("Authentication is disabled")

    yield

    deregister_worker()


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Disable logging for polling requests
        return not re.match(r".*GET /iterations/.*/next/.* 202.*", record.getMessage())


logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

app = FastAPI(lifespan=lifespan)


def get_rank():
    return app.state.rank


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
)
app.include_router(root_router)
app.include_router(datasets_router)
app.include_router(iterations_router)
app.include_router(registries_router)
