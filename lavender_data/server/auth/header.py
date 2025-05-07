from typing import Annotated, Optional
import binascii
from base64 import b64decode

from fastapi import Depends, HTTPException, Request
from fastapi.security import (
    HTTPBasic as HTTPBasicBase,
    HTTPBasicCredentials,
)
from fastapi.security.utils import get_authorization_scheme_param
from starlette.status import HTTP_401_UNAUTHORIZED
from lavender_data.server.settings import AppSettings


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
