from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_shardset_params import CreateShardsetParams
from ...models.create_shardset_response import CreateShardsetResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    dataset_id: str,
    *,
    body: CreateShardsetParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/datasets/{dataset_id}/shardsets",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[CreateShardsetResponse, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = CreateShardsetResponse.from_dict(response.json())

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
) -> Response[Union[CreateShardsetResponse, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    dataset_id: str,
    *,
    client: AuthenticatedClient,
    body: CreateShardsetParams,
) -> Response[Union[CreateShardsetResponse, HTTPValidationError]]:
    """Create Shardset

    Args:
        dataset_id (str):
        body (CreateShardsetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CreateShardsetResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    dataset_id: str,
    *,
    client: AuthenticatedClient,
    body: CreateShardsetParams,
) -> Optional[Union[CreateShardsetResponse, HTTPValidationError]]:
    """Create Shardset

    Args:
        dataset_id (str):
        body (CreateShardsetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CreateShardsetResponse, HTTPValidationError]
    """

    return sync_detailed(
        dataset_id=dataset_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    dataset_id: str,
    *,
    client: AuthenticatedClient,
    body: CreateShardsetParams,
) -> Response[Union[CreateShardsetResponse, HTTPValidationError]]:
    """Create Shardset

    Args:
        dataset_id (str):
        body (CreateShardsetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CreateShardsetResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    dataset_id: str,
    *,
    client: AuthenticatedClient,
    body: CreateShardsetParams,
) -> Optional[Union[CreateShardsetResponse, HTTPValidationError]]:
    """Create Shardset

    Args:
        dataset_id (str):
        body (CreateShardsetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CreateShardsetResponse, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            dataset_id=dataset_id,
            client=client,
            body=body,
        )
    ).parsed
