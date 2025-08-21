from datetime import datetime, timedelta
import hashlib

from fastapi import Depends, HTTPException
from sqlmodel import select, update

from lavender_data.server.distributed import CurrentCluster
from lavender_data.server.cache import CacheClient
from lavender_data.server.db import DbSession
from lavender_data.server.db.models import ApiKey
from lavender_data.server.settings import AppSettings

from .header import AuthorizationHeader


def api_key_auth(
    auth: AuthorizationHeader,
    session: DbSession,
    settings: AppSettings,
    cache: CacheClient,
    cluster: CurrentCluster,
):
    if settings.lavender_data_disable_auth:
        return None

    api_key_id = auth.username
    api_key_secret = auth.password

    cache_key = f"api_key:{hashlib.sha256((api_key_id+':'+api_key_secret).encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached:
        expires_at, locked = cached.decode("utf-8").split(";")
        expires_at = datetime.fromisoformat(expires_at)
        api_key = ApiKey(
            id=api_key_id,
            secret=api_key_secret,
            note="",
            expires_at=expires_at,
            locked=locked == "locked",
        )
    else:
        if cluster is None or cluster.is_head:
            api_key = session.exec(
                select(ApiKey).where(
                    ApiKey.id == api_key_id,
                    ApiKey.secret == api_key_secret,
                )
            ).one_or_none()
        else:
            api_key = cluster.get_api_key(api_key_id, api_key_secret)

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

    cache.set(
        cache_key,
        (
            api_key.expires_at
            if api_key.expires_at
            else datetime.now() + timedelta(days=30)
        ).isoformat()
        + ";"
        + ("locked" if api_key.locked else ""),
        ex=60 * 60,
    )

    if cluster is None or cluster.is_head:
        session.exec(
            update(ApiKey)
            .where(ApiKey.id == api_key_id)
            .values(last_accessed_at=datetime.now())
        )
        session.close()

    return api_key


ApiKeyAuth: None = Depends(api_key_auth)
