from datetime import datetime
from typing import Optional

from sqlmodel import select

from lavender_data.server.db import db_manual_session, setup_db
from lavender_data.server.db.models import ApiKey
from lavender_data.server.settings import get_settings


def create_api_key(
    note: Optional[str] = None,
    expires_at: Optional[datetime] = None,
):
    setup_db(get_settings().lavender_data_db_url)

    with db_manual_session() as session:
        api_key = None
        if note:
            api_key = session.exec(
                select(ApiKey).where(ApiKey.note == note)
            ).one_or_none()

        if api_key is None:
            api_key = ApiKey(note=note, expires_at=expires_at)
            session.add(api_key)
        else:
            api_key.expires_at = expires_at

        session.commit()
        session.refresh(api_key)

    return api_key
