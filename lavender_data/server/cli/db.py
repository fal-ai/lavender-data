from pathlib import Path

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv


def _get_config(env_file: str = ".env"):
    load_dotenv(env_file)
    db_dir = (Path(__file__).parent.parent / "db").resolve()
    config_path = db_dir / "alembic.ini"
    config = Config(config_path)
    config.set_main_option("script_location", (db_dir / "migrations").as_posix())
    return config


def makemigrations(env_file: str = ".env", message: str = ""):
    config = _get_config(env_file)
    command.revision(config, message=message, autogenerate=True)


def migrate(env_file: str = ".env"):
    config = _get_config(env_file)
    command.upgrade(config, "head")
