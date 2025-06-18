from datetime import datetime

from fastapi import Depends, HTTPException
from sqlmodel import select, update

from lavender_data.server.db import DbSession
from lavender_data.server.db.models import ApiKey
from lavender_data.server.settings import AppSettings

from .header import AuthorizationHeader


def api_key_auth(auth: AuthorizationHeader, session: DbSession, settings: AppSettings):
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

    try:
        if api_key is None:
            raise HTTPException(status_code=401, detail="Invalid API key")

        if api_key.expires_at is not None and api_key.expires_at < datetime.now():
            raise HTTPException(status_code=401, detail="API key expired")

        if api_key.locked:
            raise HTTPException(status_code=401, detail="API key is locked")
    except Exception as e:
        session.close()
        raise e

    session.exec(
        update(ApiKey)
        .where(ApiKey.id == api_key_id)
        .values(last_accessed_at=datetime.now())
    )
    session.close()

    return api_key


ApiKeyAuth: None = Depends(api_key_auth)
