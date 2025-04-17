from typing import Annotated, Optional
from datetime import datetime
import secrets
import binascii
from base64 import b64decode

from fastapi import Depends, HTTPException, Request
from fastapi.security import (
    HTTPBasic as HTTPBasicBase,
    HTTPBasicCredentials,
)
from fastapi.security.utils import get_authorization_scheme_param
from starlette.status import HTTP_401_UNAUTHORIZED
from sqlmodel import select, update

from lavender_data.server.db import DbSession
from lavender_data.server.db.models import ApiKey
from lavender_data.server.settings import AppSettings


def generate_api_key_secret():
    return secrets.token_urlsafe(32)


class HTTPBasic(HTTPBasicBase):
    async def __call__(  # type: ignore
        self,
        request: Request,
        settings: AppSettings,
    ) -> Optional[HTTPBasicCredentials]:
        if settings.lavender_data_disable_auth:
            return None

        authorization = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if self.realm:
            unauthorized_headers = {"WWW-Authenticate": f'Basic realm="{self.realm}"'}
        else:
            unauthorized_headers = {"WWW-Authenticate": "Basic"}
        if not authorization or scheme.lower() != "basic":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers=unauthorized_headers,
                )
            else:
                return None
        invalid_user_credentials_exc = HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers=unauthorized_headers,
        )
        try:
            data = b64decode(param).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error):
            raise invalid_user_credentials_exc  # noqa: B904
        username, separator, password = data.partition(":")
        if not separator:
            raise invalid_user_credentials_exc
        return HTTPBasicCredentials(username=username, password=password)


http_basic = HTTPBasic()


AuthorizationHeader = Annotated[HTTPBasicCredentials, Depends(http_basic)]


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
