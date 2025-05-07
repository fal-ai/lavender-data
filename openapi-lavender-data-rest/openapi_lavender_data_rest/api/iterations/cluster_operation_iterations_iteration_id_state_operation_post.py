from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.cluster_operation_iterations_iteration_id_state_operation_post_params import (
    ClusterOperationIterationsIterationIdStateOperationPostParams,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    iteration_id: str,
    operation: str,
    *,
    body: ClusterOperationIterationsIterationIdStateOperationPostParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/iterations/{iteration_id}/state/{operation}",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = response.json()
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
) -> Response[Union[Any, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    iteration_id: str,
    operation: str,
    *,
    client: AuthenticatedClient,
    body: ClusterOperationIterationsIterationIdStateOperationPostParams,
) -> Response[Union[Any, HTTPValidationError]]:
    """Cluster Operation

    Args:
        iteration_id (str):
        operation (str):
        body (ClusterOperationIterationsIterationIdStateOperationPostParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        iteration_id=iteration_id,
        operation=operation,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    iteration_id: str,
    operation: str,
    *,
    client: AuthenticatedClient,
    body: ClusterOperationIterationsIterationIdStateOperationPostParams,
) -> Optional[Union[Any, HTTPValidationError]]:
    """Cluster Operation

    Args:
        iteration_id (str):
        operation (str):
        body (ClusterOperationIterationsIterationIdStateOperationPostParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return sync_detailed(
        iteration_id=iteration_id,
        operation=operation,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    iteration_id: str,
    operation: str,
    *,
    client: AuthenticatedClient,
    body: ClusterOperationIterationsIterationIdStateOperationPostParams,
) -> Response[Union[Any, HTTPValidationError]]:
    """Cluster Operation

    Args:
        iteration_id (str):
        operation (str):
        body (ClusterOperationIterationsIterationIdStateOperationPostParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        iteration_id=iteration_id,
        operation=operation,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    iteration_id: str,
    operation: str,
    *,
    client: AuthenticatedClient,
    body: ClusterOperationIterationsIterationIdStateOperationPostParams,
) -> Optional[Union[Any, HTTPValidationError]]:
    """Cluster Operation

    Args:
        iteration_id (str):
        operation (str):
        body (ClusterOperationIterationsIterationIdStateOperationPostParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            iteration_id=iteration_id,
            operation=operation,
            client=client,
            body=body,
        )
    ).parsed
