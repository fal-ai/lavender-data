from http import HTTPStatus
from io import BytesIO
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, File, Response, Unset


def _get_kwargs(
    iteration_id: str,
    *,
    rank: Union[Unset, int] = 0,
    async_mode: Union[Unset, bool] = False,
    no_cache: Union[Unset, bool] = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["rank"] = rank

    params["async_mode"] = async_mode

    params["no_cache"] = no_cache

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/iterations/{iteration_id}/next",
        "params": params,
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
    *,
    client: AuthenticatedClient,
    rank: Union[Unset, int] = 0,
    async_mode: Union[Unset, bool] = False,
    no_cache: Union[Unset, bool] = False,
) -> Response[Union[File, HTTPValidationError]]:
    """Get Next

    Args:
        iteration_id (str):
        rank (Union[Unset, int]):  Default: 0.
        async_mode (Union[Unset, bool]):  Default: False.
        no_cache (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[File, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        iteration_id=iteration_id,
        rank=rank,
        async_mode=async_mode,
        no_cache=no_cache,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    iteration_id: str,
    *,
    client: AuthenticatedClient,
    rank: Union[Unset, int] = 0,
    async_mode: Union[Unset, bool] = False,
    no_cache: Union[Unset, bool] = False,
) -> Optional[Union[File, HTTPValidationError]]:
    """Get Next

    Args:
        iteration_id (str):
        rank (Union[Unset, int]):  Default: 0.
        async_mode (Union[Unset, bool]):  Default: False.
        no_cache (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[File, HTTPValidationError]
    """

    return sync_detailed(
        iteration_id=iteration_id,
        client=client,
        rank=rank,
        async_mode=async_mode,
        no_cache=no_cache,
    ).parsed


async def asyncio_detailed(
    iteration_id: str,
    *,
    client: AuthenticatedClient,
    rank: Union[Unset, int] = 0,
    async_mode: Union[Unset, bool] = False,
    no_cache: Union[Unset, bool] = False,
) -> Response[Union[File, HTTPValidationError]]:
    """Get Next

    Args:
        iteration_id (str):
        rank (Union[Unset, int]):  Default: 0.
        async_mode (Union[Unset, bool]):  Default: False.
        no_cache (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[File, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        iteration_id=iteration_id,
        rank=rank,
        async_mode=async_mode,
        no_cache=no_cache,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    iteration_id: str,
    *,
    client: AuthenticatedClient,
    rank: Union[Unset, int] = 0,
    async_mode: Union[Unset, bool] = False,
    no_cache: Union[Unset, bool] = False,
) -> Optional[Union[File, HTTPValidationError]]:
    """Get Next

    Args:
        iteration_id (str):
        rank (Union[Unset, int]):  Default: 0.
        async_mode (Union[Unset, bool]):  Default: False.
        no_cache (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[File, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            iteration_id=iteration_id,
            client=client,
            rank=rank,
            async_mode=async_mode,
            no_cache=no_cache,
        )
    ).parsed
