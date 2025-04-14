from http import HTTPStatus
from io import BytesIO
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import File, Response


def _get_kwargs(
    iteration_id: str,
    cache_key: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/iterations/{iteration_id}/next/{cache_key}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[File, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = File(payload=BytesIO(response.content))

        return response_200
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[File, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    iteration_id: str,
    cache_key: str,
    *,
    client: AuthenticatedClient,
) -> Response[Union[File, HTTPValidationError]]:
    """Get Next Async Result

    Args:
        iteration_id (str):
        cache_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[File, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        iteration_id=iteration_id,
        cache_key=cache_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    iteration_id: str,
    cache_key: str,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[File, HTTPValidationError]]:
    """Get Next Async Result

    Args:
        iteration_id (str):
        cache_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[File, HTTPValidationError]
    """

    return sync_detailed(
        iteration_id=iteration_id,
        cache_key=cache_key,
        client=client,
    ).parsed


async def asyncio_detailed(
    iteration_id: str,
    cache_key: str,
    *,
    client: AuthenticatedClient,
) -> Response[Union[File, HTTPValidationError]]:
    """Get Next Async Result

    Args:
        iteration_id (str):
        cache_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[File, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        iteration_id=iteration_id,
        cache_key=cache_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    iteration_id: str,
    cache_key: str,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[File, HTTPValidationError]]:
    """Get Next Async Result

    Args:
        iteration_id (str):
        cache_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[File, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            iteration_id=iteration_id,
            cache_key=cache_key,
            client=client,
        )
    ).parsed
