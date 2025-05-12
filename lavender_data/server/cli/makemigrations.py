from alembic import command
from alembic.config import Config
from dotenv import load_dotenv


def makemigrations(env_file: str = ".env", message: str = ""):
    load_dotenv(env_file)
    config = Config("alembic.ini")
    command.revision(config, message=message, autogenerate=True)
