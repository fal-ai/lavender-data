from datetime import datetime
from typing import Optional

from lavender_data.server.auth import generate_api_key_secret
from lavender_data.server.db import get_session, setup_db
from lavender_data.server.db.models import ApiKey
from lavender_data.server.settings import get_settings


def create_api_key(
    note: Optional[str] = None,
    expires_at: Optional[datetime] = None,
):
    setup_db(get_settings().lavender_data_db_url)
    session = next(get_session())

    api_key = ApiKey(secret=generate_api_key_secret(), note=note, expires_at=expires_at)
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return api_key
