from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.submit_next_response import SubmitNextResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    iteration_id: str,
    *,
    rank: Union[Unset, int] = 0,
    no_cache: Union[Unset, bool] = False,
    max_retry_count: Union[Unset, int] = 0,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["rank"] = rank

    params["no_cache"] = no_cache

    params["max_retry_count"] = max_retry_count

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/iterations/{iteration_id}/next",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, SubmitNextResponse]]:
    if response.status_code == 200:
        response_200 = SubmitNextResponse.from_dict(response.json())

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
) -> Response[Union[HTTPValidationError, SubmitNextResponse]]:
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
    no_cache: Union[Unset, bool] = False,
    max_retry_count: Union[Unset, int] = 0,
) -> Response[Union[HTTPValidationError, SubmitNextResponse]]:
    """Submit Next

    Args:
        iteration_id (str):
        rank (Union[Unset, int]):  Default: 0.
        no_cache (Union[Unset, bool]):  Default: False.
        max_retry_count (Union[Unset, int]):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, SubmitNextResponse]]
    """

    kwargs = _get_kwargs(
        iteration_id=iteration_id,
        rank=rank,
        no_cache=no_cache,
        max_retry_count=max_retry_count,
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
    no_cache: Union[Unset, bool] = False,
    max_retry_count: Union[Unset, int] = 0,
) -> Optional[Union[HTTPValidationError, SubmitNextResponse]]:
    """Submit Next

    Args:
        iteration_id (str):
        rank (Union[Unset, int]):  Default: 0.
        no_cache (Union[Unset, bool]):  Default: False.
        max_retry_count (Union[Unset, int]):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, SubmitNextResponse]
    """

    return sync_detailed(
        iteration_id=iteration_id,
        client=client,
        rank=rank,
        no_cache=no_cache,
        max_retry_count=max_retry_count,
    ).parsed


async def asyncio_detailed(
    iteration_id: str,
    *,
    client: AuthenticatedClient,
    rank: Union[Unset, int] = 0,
    no_cache: Union[Unset, bool] = False,
    max_retry_count: Union[Unset, int] = 0,
) -> Response[Union[HTTPValidationError, SubmitNextResponse]]:
    """Submit Next

    Args:
        iteration_id (str):
        rank (Union[Unset, int]):  Default: 0.
        no_cache (Union[Unset, bool]):  Default: False.
        max_retry_count (Union[Unset, int]):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, SubmitNextResponse]]
    """

    kwargs = _get_kwargs(
        iteration_id=iteration_id,
        rank=rank,
        no_cache=no_cache,
        max_retry_count=max_retry_count,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    iteration_id: str,
    *,
    client: AuthenticatedClient,
    rank: Union[Unset, int] = 0,
    no_cache: Union[Unset, bool] = False,
    max_retry_count: Union[Unset, int] = 0,
) -> Optional[Union[HTTPValidationError, SubmitNextResponse]]:
    """Submit Next

    Args:
        iteration_id (str):
        rank (Union[Unset, int]):  Default: 0.
        no_cache (Union[Unset, bool]):  Default: False.
        max_retry_count (Union[Unset, int]):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, SubmitNextResponse]
    """

    return (
        await asyncio_detailed(
            iteration_id=iteration_id,
            client=client,
            rank=rank,
            no_cache=no_cache,
            max_retry_count=max_retry_count,
        )
    ).parsed
