import os
from typing import Annotated, Optional

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import QueuePool

from lavender_data.logging import get_logger
from lavender_data.server.settings import root_dir


engine = None


def default_db_url():
    db_path = os.path.join(root_dir, "database.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return f"sqlite:///{db_path}"


def setup_db(db_url: Optional[str] = None):
    global engine

    connect_args = {}
    kwargs = {}

    if not db_url:
        db_url = default_db_url()
        get_logger(__name__).debug(f"LAVENDER_DATA_DB_URL is not set, using {db_url}")

    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        kwargs["poolclass"] = QueuePool

    if db_url.startswith("postgres"):
        try:
            import psycopg2
        except ImportError:
            raise ImportError(
                "Please install required dependencies for PostgresStorage. "
                "You can install them with `pip install lavender-data[pgsql]`"
            )

    engine = create_engine(db_url, connect_args=connect_args, **kwargs)


def get_session():
    if not engine:
        raise RuntimeError("Database not initialized")

    with Session(engine) as session:
        yield session


def db_manual_session(**options):
    if not engine:
        raise RuntimeError("Database not initialized")

    return Session(engine, **options)


DbSession = Annotated[Session, Depends(get_session)]
