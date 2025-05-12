from alembic import command
from alembic.config import Config
from dotenv import load_dotenv


def migrate(env_file: str = ".env"):
    load_dotenv(env_file)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
