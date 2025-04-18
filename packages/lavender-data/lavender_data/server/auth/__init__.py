from typing import Optional
from datetime import datetime

from fastapi import Depends, HTTPException
from sqlmodel import select, update

from lavender_data.server.db import DbSession
from lavender_data.server.db.models import ApiKey
from lavender_data.server.settings import AppSettings

from .header import AuthorizationHeader


def get_current_api_key(
    auth: AuthorizationHeader, session: DbSession, settings: AppSettings
):
    if settings.lavender_data_disable_auth:
        return None

    api_key_id = auth.username
    api_key_secret = auth.password

    api_key = session.exec(
        select(ApiKey).where(
            ApiKey.id == api_key_id,
            ApiKey.secret == api_key_secret,
        )
    ).one_or_none()

    if api_key is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if api_key.expires_at is not None and api_key.expires_at < datetime.now():
        raise HTTPException(status_code=401, detail="API key expired")

    if api_key.locked:
        raise HTTPException(status_code=401, detail="API key is locked")

    session.exec(
        update(ApiKey)
        .where(ApiKey.id == api_key_id)
        .values(last_accessed_at=datetime.now())
    )

    return api_key


CurrentApiKey: Optional[ApiKey] = Depends(get_current_api_key)
