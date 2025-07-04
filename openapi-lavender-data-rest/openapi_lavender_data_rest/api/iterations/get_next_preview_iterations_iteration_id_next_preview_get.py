from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_next_preview_iterations_iteration_id_next_preview_get_response_get_next_preview_iterations_iteration_id_next_preview_get import (
    GetNextPreviewIterationsIterationIdNextPreviewGetResponseGetNextPreviewIterationsIterationIdNextPreviewGet,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    iteration_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/iterations/{iteration_id}/next-preview",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        GetNextPreviewIterationsIterationIdNextPreviewGetResponseGetNextPreviewIterationsIterationIdNextPreviewGet,
        HTTPValidationError,
    ]
]:
    if response.status_code == 200:
        response_200 = GetNextPreviewIterationsIterationIdNextPreviewGetResponseGetNextPreviewIterationsIterationIdNextPreviewGet.from_dict(
            response.json()
        )

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
) -> Response[
    Union[
        GetNextPreviewIterationsIterationIdNextPreviewGetResponseGetNextPreviewIterationsIterationIdNextPreviewGet,
        HTTPValidationError,
    ]
]:
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
) -> Response[
    Union[
        GetNextPreviewIterationsIterationIdNextPreviewGetResponseGetNextPreviewIterationsIterationIdNextPreviewGet,
        HTTPValidationError,
    ]
]:
    """Get Next Preview

    Args:
        iteration_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetNextPreviewIterationsIterationIdNextPreviewGetResponseGetNextPreviewIterationsIterationIdNextPreviewGet, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        iteration_id=iteration_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    iteration_id: str,
    *,
    client: AuthenticatedClient,
) -> Optional[
    Union[
        GetNextPreviewIterationsIterationIdNextPreviewGetResponseGetNextPreviewIterationsIterationIdNextPreviewGet,
        HTTPValidationError,
    ]
]:
    """Get Next Preview

    Args:
        iteration_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetNextPreviewIterationsIterationIdNextPreviewGetResponseGetNextPreviewIterationsIterationIdNextPreviewGet, HTTPValidationError]
    """

    return sync_detailed(
        iteration_id=iteration_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    iteration_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[
    Union[
        GetNextPreviewIterationsIterationIdNextPreviewGetResponseGetNextPreviewIterationsIterationIdNextPreviewGet,
        HTTPValidationError,
    ]
]:
    """Get Next Preview

    Args:
        iteration_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetNextPreviewIterationsIterationIdNextPreviewGetResponseGetNextPreviewIterationsIterationIdNextPreviewGet, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        iteration_id=iteration_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    iteration_id: str,
    *,
    client: AuthenticatedClient,
) -> Optional[
    Union[
        GetNextPreviewIterationsIterationIdNextPreviewGetResponseGetNextPreviewIterationsIterationIdNextPreviewGet,
        HTTPValidationError,
    ]
]:
    """Get Next Preview

    Args:
        iteration_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetNextPreviewIterationsIterationIdNextPreviewGetResponseGetNextPreviewIterationsIterationIdNextPreviewGet, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            iteration_id=iteration_id,
            client=client,
        )
    ).parsed
