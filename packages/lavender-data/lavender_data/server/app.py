import re
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lavender_data.logging import get_logger

from .ui import setup_ui
from .db import setup_db, create_db_and_tables
from .cache import setup_cache, register_worker, deregister_worker
from .distributed import setup_cluster, cleanup_cluster
from .reader import setup_reader
from .routes import (
    datasets_router,
    iterations_router,
    registries_router,
    cluster_router,
    root_router,
)

from .services.registries import import_from_directory
from .settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = get_logger(__name__)
    settings = get_settings()

    setup_db(settings.lavender_data_db_url)
    create_db_and_tables()

    setup_cache(redis_url=settings.lavender_data_redis_url)

    if settings.lavender_data_modules_dir:
        import_from_directory(settings.lavender_data_modules_dir)

    setup_reader(settings.lavender_data_reader_disk_cache_size)

    rank = register_worker()
    app.state.rank = rank

    if settings.lavender_data_cluster_enabled:
        setup_cluster(
            head_url=settings.lavender_data_cluster_head_url,
            node_url=settings.lavender_data_cluster_node_url,
            secret=settings.lavender_data_cluster_secret,
            disable_auth=settings.lavender_data_disable_auth,
        )

    if settings.lavender_data_disable_ui:
        logger.warning("UI is disabled")
        ui = None
    else:
        try:
            ui = setup_ui(
                f"http://{settings.lavender_data_host}:{settings.lavender_data_port}",
                settings.lavender_data_ui_port,
            )
        except Exception as e:
            logger.warning(f"UI failed to start: {e}")

    if settings.lavender_data_disable_auth:
        logger.warning("Authentication is disabled")

    yield

    # TODO dump and load iteration states

    if settings.lavender_data_cluster_enabled:
        cleanup_cluster()

    try:
        if ui is not None:
            ui.terminate()
    except Exception as e:
        pass

    deregister_worker()


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Disable logging for polling requests
        return not re.match(r".*GET.*/iterations/.*/next/.* 202.*", record.getMessage())


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
app.include_router(cluster_router)
