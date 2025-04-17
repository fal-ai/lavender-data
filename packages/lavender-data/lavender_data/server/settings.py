from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings
from lavender_data.logging import get_logger

logger = get_logger(__name__)


class Settings(BaseSettings, extra="ignore"):
    lavender_data_modules_dir: str = ""
    lavender_data_db_url: str = ""
    lavender_data_redis_url: str = ""
    lavender_data_reader_disk_cache_size: int = 4 * 1024**3  # 4GB
    lavender_data_batch_cache_ttl: int = 5 * 60
    lavender_data_disable_auth: bool = False

    lavender_data_cluster_enabled: bool = False
    lavender_data_cluster_secret: str = ""
    lavender_data_cluster_head_url: str = "http://127.0.0.1:8000"
    lavender_data_cluster_node_url: str = ""


@lru_cache
def get_settings():
    logger.info("Loading settings")
    return Settings()


AppSettings = Annotated[Settings, Depends(get_settings)]
