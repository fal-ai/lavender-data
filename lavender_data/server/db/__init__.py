import os
from typing import Annotated, Optional

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from lavender_data.logging import get_logger
from .models import Dataset, Shardset, DatasetColumn, Iteration, Shard


engine = None


def default_db_url():
    db_path = os.path.expanduser("~/.lavender-data/database.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return f"sqlite:///{db_path}"


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def setup_db(db_url: Optional[str] = None):
    global engine

    connect_args = {}

    if not db_url:
        db_url = default_db_url()
        get_logger(__name__).debug(f"LAVENDER_DATA_DB_URL is not set, using {db_url}")
        connect_args = {"check_same_thread": False}

    if db_url.startswith("postgres"):
        try:
            import psycopg2
        except ImportError:
            raise ImportError(
                "Please install required dependencies for PostgresStorage. "
                "You can install them with `pip install lavender-data[pgsql]`"
            )

    engine = create_engine(db_url, connect_args=connect_args)
    create_db_and_tables()


def get_session():
    if not engine:
        raise RuntimeError("Database not initialized")

    with Session(engine) as session:
        yield session


DbSession = Annotated[Session, Depends(get_session)]
