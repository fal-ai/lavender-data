from typing import Annotated, Optional
from datetime import datetime
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel import select, update

from lavender_data.server.db import DbSession
from lavender_data.server.db.models import ApiKey

http_basic = HTTPBasic()


AuthorizationHeader = Annotated[HTTPBasicCredentials, Depends(http_basic)]


def get_current_api_key(auth: AuthorizationHeader, session: DbSession):
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


CurrentApiKey: ApiKey = Depends(get_current_api_key)


def generate_api_key_secret():
    return secrets.token_urlsafe(32)
