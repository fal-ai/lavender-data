import re
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lavender_data.logging import get_logger

from .ui import setup_ui
from .db import setup_db
from .cache import setup_cache
from .distributed import setup_cluster, cleanup_cluster, get_cluster
from .reader import setup_reader
from .background_worker import setup_background_worker, shutdown_background_worker
from .routes import (
    datasets_router,
    iterations_router,
    registries_router,
    cluster_router,
    root_router,
    background_tasks_router,
)

from .registries import setup_registries
from .settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = get_logger(__name__)
    settings = get_settings()

    setup_db(settings.lavender_data_db_url)

    setup_cache(redis_url=settings.lavender_data_redis_url)

    setup_registries(settings.lavender_data_modules_dir)

    setup_reader(settings.lavender_data_reader_disk_cache_size)

    setup_cluster(
        enabled=settings.lavender_data_cluster_enabled,
        head_url=settings.lavender_data_cluster_head_url,
        node_url=settings.lavender_data_cluster_node_url,
        secret=settings.lavender_data_cluster_secret,
        disable_auth=settings.lavender_data_disable_auth,
    )

    cluster = get_cluster()
    if cluster is not None:
        cluster.start()

    setup_background_worker(settings.lavender_data_num_workers)

    if settings.lavender_data_disable_ui:
        logger.warning("UI is disabled")
        ui = None
    else:
        try:
            ui = setup_ui(
                f"http://{settings.lavender_data_host}:{settings.lavender_data_port}",
                settings.lavender_data_ui_port,
                force_install_dependencies=settings.lavender_data_ui_force_install_dependencies,
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

    try:
        shutdown_background_worker()
    except Exception as e:
        pass


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Disable logging for polling requests
        return not re.match(r".*GET.*/iterations/.*/next/.* 202.*", record.getMessage())


logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

app = FastAPI(lifespan=lifespan)


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
app.include_router(background_tasks_router)
