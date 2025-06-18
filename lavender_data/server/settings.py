import os
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings
from lavender_data.logging import get_logger

root_dir = os.path.expanduser("~/.lavender-data")
files_dir = os.path.join(root_dir, "files")
os.makedirs(files_dir, exist_ok=True)


class Settings(BaseSettings, extra="ignore"):
    lavender_data_port: int = 8000
    lavender_data_host: str = "0.0.0.0"
    lavender_data_ui_port: int = 3000
    lavender_data_ui_force_install_dependencies: bool = False
    lavender_data_disable_ui: bool = False
    lavender_data_disable_auth: bool = False
    lavender_data_num_workers: int = 0

    lavender_data_modules_dir: str = ""
    lavender_data_modules_reload_interval: int = 10

    lavender_data_db_url: str = ""
    lavender_data_redis_url: str = ""
    lavender_data_reader_disk_cache_size: int = 4 * 1024**3  # 4GB
    lavender_data_batch_cache_ttl: int = 5 * 60

    lavender_data_cluster_enabled: bool = False
    lavender_data_cluster_secret: str = ""
    lavender_data_cluster_head_url: str = ""
    lavender_data_cluster_node_url: str = ""


@lru_cache
def get_settings():
    get_logger(__name__).debug("Loading settings")
    return Settings()


AppSettings = Annotated[Settings, Depends(get_settings)]
