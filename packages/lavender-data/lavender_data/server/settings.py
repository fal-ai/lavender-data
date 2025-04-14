from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings


class Settings(BaseSettings, extra="ignore"):
    lavender_data_modules_dir: str = ""
    lavender_data_db_url: str = ""
    lavender_data_redis_url: str = ""
    lavender_data_reader_disk_cache_size: str = "100"
    lavender_data_batch_cache_ttl: int = 5 * 60
    lavender_data_disable_auth: bool = False

    class Config:
        env_file = ".env"


settings = Settings()


def get_settings():
    return settings


AppSettings = Annotated[Settings, Depends(get_settings)]
