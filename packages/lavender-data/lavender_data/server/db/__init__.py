from typing import Annotated, Optional

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from lavender_data.logging import get_logger
from .models import Dataset, Shardset, DatasetColumn, Iteration, Shard


engine = None


def setup_db(db_url: Optional[str] = None):
    global engine

    connect_args = {}

    if not db_url:
        get_logger(__name__).warning(
            "LAVENDER_DATA_DB_URL is not set, using sqlite:///database.db"
        )
        db_url = f"sqlite:///database.db"
        connect_args = {"check_same_thread": False}

    engine = create_engine(db_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    if not engine:
        raise RuntimeError("Database not initialized")

    with Session(engine) as session:
        yield session


DbSession = Annotated[Session, Depends(get_session)]
