from typing import Optional, TypeVar, Union
from contextlib import contextmanager
import base64
import os

from lavender_data.serialize import deserialize_sample

from openapi_lavender_data_rest import Client, AuthenticatedClient
from openapi_lavender_data_rest.types import Response

# apis
from openapi_lavender_data_rest.api.root import version_version_get
from openapi_lavender_data_rest.api.datasets import (
    get_dataset_datasets_dataset_id_get,
    get_datasets_datasets_get,
    get_shardset_datasets_dataset_id_shardsets_shardset_id_get,
    create_dataset_datasets_post,
    create_shardset_datasets_dataset_id_shardsets_post,
    sync_shardset_datasets_dataset_id_shardsets_shardset_id_sync_post,
    get_sync_status_datasets_dataset_id_shardsets_shardset_id_sync_get,
)
from openapi_lavender_data_rest.api.iterations import (
    create_iteration_iterations_post,
    get_next_iterations_iteration_id_next_get,
    submit_next_iterations_iteration_id_next_post,
    get_submitted_result_iterations_iteration_id_next_cache_key_get,
    get_iteration_iterations_iteration_id_get,
    get_iterations_iterations_get,
    complete_index_iterations_iteration_id_complete_index_post,
    pushback_iterations_iteration_id_pushback_post,
    get_progress_iterations_iteration_id_progress_get,
)
from openapi_lavender_data_rest.api.cluster import (
    get_nodes_cluster_nodes_get,
)

# models
from openapi_lavender_data_rest.models.http_validation_error import HTTPValidationError
from openapi_lavender_data_rest.models.create_dataset_params import CreateDatasetParams
from openapi_lavender_data_rest.models.create_shardset_params import (
    CreateShardsetParams,
)
from openapi_lavender_data_rest.models.sync_shardset_params import SyncShardsetParams
from openapi_lavender_data_rest.models.dataset_column_options import (
    DatasetColumnOptions,
)
from openapi_lavender_data_rest.models.get_dataset_response import GetDatasetResponse
from openapi_lavender_data_rest.models.create_iteration_params import (
    CreateIterationParams,
)
from openapi_lavender_data_rest.models.get_iteration_response import (
    GetIterationResponse,
)
from openapi_lavender_data_rest.models.dataset_public import DatasetPublic
from openapi_lavender_data_rest.models.dataset_column_public import DatasetColumnPublic
from openapi_lavender_data_rest.models.shardset_public import ShardsetPublic
from openapi_lavender_data_rest.models.shardset_with_shards import ShardsetWithShards
from openapi_lavender_data_rest.models.shard_public import ShardPublic
from openapi_lavender_data_rest.models.iteration_filter import IterationFilter
from openapi_lavender_data_rest.models.iteration_preprocessor import (
    IterationPreprocessor,
)
from openapi_lavender_data_rest.models.iteration_collater import IterationCollater


class LavenderDataApiError(Exception):
    pass


_T = TypeVar("T")


class LavenderDataClient:
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.api_url = api_url or os.getenv("LAVENDER_DATA_API_URL")
        self.api_key = api_key or os.getenv("LAVENDER_DATA_API_KEY")

        try:
            self.version = self.get_version().version
        except Exception as e:
            raise ValueError(
                "Failed to initialize lavender_data client. Please check if the server is running."
            ) from e

    @contextmanager
    def _get_client(self):
        if self.api_key is None:
            _client = Client(base_url=self.api_url)
        else:
            _client = AuthenticatedClient(
                base_url=self.api_url,
                token=base64.b64encode(self.api_key.encode()).decode(),
                prefix="Basic",
            )
        with _client as client:
            yield client

    def _check_response(self, response: Response[Union[_T, HTTPValidationError]]) -> _T:
        if response.status_code >= 400:
            raise LavenderDataApiError(response.content.decode("utf-8"))
        if isinstance(response.parsed, HTTPValidationError):
            raise LavenderDataApiError(response.parsed)
        return response.parsed

    def get_version(self):
        with self._get_client() as client:
            response = version_version_get.sync_detailed(
                client=client,
            )
        return self._check_response(response)

    def get_dataset(
        self,
        dataset_id: Optional[str] = None,
        name: Optional[str] = None,
    ):
        if dataset_id is None and name is None:
            raise ValueError("Either dataset_id or name must be provided")

        if dataset_id is not None and name is not None:
            raise ValueError("Only one of dataset_id or name can be provided")

        if name is not None:
            datasets = self.get_datasets(name=name)
            if len(datasets) == 0:
                raise ValueError(f"Dataset {name} not found")

            if len(datasets) > 1:
                raise ValueError(
                    f"Multiple datasets found for name {name}: {', '.join([d.id for d in datasets])}\n"
                    "This should never happen since the dataset name is unique. "
                    "Please contact the Lavender Data team if you see this error."
                )

            dataset_id = datasets[0].id

        with self._get_client() as client:
            response = get_dataset_datasets_dataset_id_get.sync_detailed(
                client=client,
                dataset_id=dataset_id,
            )
        return self._check_response(response)

    def get_datasets(self, name: Optional[str] = None):
        with self._get_client() as client:
            response = get_datasets_datasets_get.sync_detailed(
                client=client,
                name=name,
            )
        return self._check_response(response)

    def create_dataset(self, name: str, uid_column_name: Optional[str] = None):
        with self._get_client() as client:
            response = create_dataset_datasets_post.sync_detailed(
                client=client,
                body=CreateDatasetParams(
                    name=name,
                    uid_column_name=uid_column_name,
                ),
            )
        return self._check_response(response)

    def get_shardset(self, dataset_id: str, shardset_id: str):
        with self._get_client() as client:
            response = get_shardset_datasets_dataset_id_shardsets_shardset_id_get.sync_detailed(
                client=client,
                dataset_id=dataset_id,
                shardset_id=shardset_id,
            )
        return self._check_response(response)

    def create_shardset(
        self, dataset_id: str, location: str, columns: list[DatasetColumnOptions] = []
    ):
        with self._get_client() as client:
            response = create_shardset_datasets_dataset_id_shardsets_post.sync_detailed(
                client=client,
                dataset_id=dataset_id,
                body=CreateShardsetParams(location=location, columns=columns),
            )
        return self._check_response(response)

    def sync_shardset(self, dataset_id: str, shardset_id: str, overwrite: bool = False):
        with self._get_client() as client:
            response = sync_shardset_datasets_dataset_id_shardsets_shardset_id_sync_post.sync_detailed(
                client=client,
                dataset_id=dataset_id,
                shardset_id=shardset_id,
                body=SyncShardsetParams(
                    overwrite=overwrite,
                ),
            )
        return self._check_response(response)

    def get_sync_shardset_status(self, dataset_id: str, shardset_id: str):
        with self._get_client() as client:
            response = get_sync_status_datasets_dataset_id_shardsets_shardset_id_sync_get.sync_detailed(
                client=client,
                dataset_id=dataset_id,
                shardset_id=shardset_id,
            )
        return self._check_response(response)

    def create_iteration(
        self,
        dataset_id: str,
        shardsets: Optional[list[str]] = None,
        shuffle: bool = False,
        shuffle_seed: Optional[int] = None,
        shuffle_block_size: Optional[int] = None,
        batch_size: Optional[int] = None,
        replication_pg: Optional[list[list[int]]] = None,
        filters: Optional[list[IterationFilter]] = None,
        preprocessors: Optional[list[IterationPreprocessor]] = None,
        collater: Optional[IterationCollater] = None,
        rank: int = 0,
        world_size: Optional[int] = None,
        wait_participant_threshold: Optional[float] = None,
        cluster_sync: bool = False,
    ):
        with self._get_client() as client:
            response = create_iteration_iterations_post.sync_detailed(
                client=client,
                body=CreateIterationParams(
                    dataset_id=dataset_id,
                    shardsets=shardsets,
                    shuffle=shuffle,
                    shuffle_seed=shuffle_seed,
                    shuffle_block_size=shuffle_block_size,
                    batch_size=batch_size,
                    preprocessors=preprocessors,
                    filters=filters,
                    collater=collater,
                    replication_pg=replication_pg,
                    rank=rank,
                    world_size=world_size,
                    wait_participant_threshold=wait_participant_threshold,
                    cluster_sync=cluster_sync,
                ),
            )
        return self._check_response(response)

    def get_iterations(
        self, dataset_id: Optional[str] = None, dataset_name: Optional[str] = None
    ):
        if dataset_id is None and dataset_name is None:
            raise ValueError("Either dataset_id or dataset_name must be provided")

        if dataset_id is not None and dataset_name is not None:
            raise ValueError("Only one of dataset_id or dataset_name can be provided")

        if dataset_name is not None:
            dataset = self.get_dataset(name=dataset_name)
            if dataset is None:
                raise ValueError(f"Dataset {dataset_name} not found")
            dataset_id = dataset.id

        with self._get_client() as client:
            response = get_iterations_iterations_get.sync_detailed(
                client=client,
                dataset_id=dataset_id,
            )
        return self._check_response(response)

    def get_iteration(self, iteration_id: str):
        with self._get_client() as client:
            response = get_iteration_iterations_iteration_id_get.sync_detailed(
                client=client,
                iteration_id=iteration_id,
            )
        return self._check_response(response)

    def get_next_item(
        self,
        iteration_id: str,
        rank: int = 0,
        no_cache: bool = False,
    ):
        with self._get_client() as client:
            response = get_next_iterations_iteration_id_next_get.sync_detailed(
                client=client,
                iteration_id=iteration_id,
                rank=rank,
                no_cache=no_cache,
            )
        content = self._check_response(response).payload.read()
        return deserialize_sample(content)

    def submit_next_item(
        self,
        iteration_id: str,
        rank: int = 0,
        no_cache: bool = False,
    ):
        with self._get_client() as client:
            response = submit_next_iterations_iteration_id_next_post.sync_detailed(
                client=client,
                iteration_id=iteration_id,
                rank=rank,
                no_cache=no_cache,
            )
        return self._check_response(response)

    def get_submitted_result(self, iteration_id: str, cache_key: str):
        with self._get_client() as client:
            response = get_submitted_result_iterations_iteration_id_next_cache_key_get.sync_detailed(
                client=client,
                iteration_id=iteration_id,
                cache_key=cache_key,
            )
        if response.status_code == 202:
            raise LavenderDataApiError(response.content.decode("utf-8"))
        content = self._check_response(response).payload.read()
        return deserialize_sample(content)

    def complete_index(self, iteration_id: str, index: int):
        with self._get_client() as client:
            response = complete_index_iterations_iteration_id_complete_index_post.sync_detailed(
                client=client,
                iteration_id=iteration_id,
                index=index,
            )
        return self._check_response(response)

    def pushback(self, iteration_id: str):
        with self._get_client() as client:
            response = pushback_iterations_iteration_id_pushback_post.sync_detailed(
                client=client,
                iteration_id=iteration_id,
            )
        return self._check_response(response)

    def get_progress(self, iteration_id: str):
        with self._get_client() as client:
            response = get_progress_iterations_iteration_id_progress_get.sync_detailed(
                client=client,
                iteration_id=iteration_id,
            )
        return self._check_response(response)

    def get_node_statuses(self):
        with self._get_client() as client:
            response = get_nodes_cluster_nodes_get.sync_detailed(
                client=client,
            )
        return self._check_response(response)


_client_instance = None


@contextmanager
def ensure_client():
    global _client_instance
    if _client_instance is None:
        try:
            init(
                api_url=os.getenv("LAVENDER_DATA_API_URL", "http://localhost:8000"),
                api_key=os.getenv("LAVENDER_DATA_API_KEY", None),
            )
        except Exception as e:
            raise e
    yield _client_instance


def init(api_url: str = "http://localhost:8000", api_key: Optional[str] = None):
    """Initialize and return a LavenderDataClient instance.

    This function maintains backwards compatibility with the old API.
    """
    global _client_instance
    _client_instance = LavenderDataClient(api_url=api_url, api_key=api_key)
    return _client_instance


def get_client():
    global _client_instance
    if _client_instance is None:
        raise ValueError(
            "Lavender Data client is not initialized. Please call lavender_data.client.api.init() first."
        )
    return _client_instance


@ensure_client()
def get_version():
    return _client_instance.get_version()


@ensure_client()
def get_dataset(
    dataset_id: Optional[str] = None,
    name: Optional[str] = None,
):
    return _client_instance.get_dataset(dataset_id=dataset_id, name=name)


@ensure_client()
def get_datasets(name: Optional[str] = None):
    return _client_instance.get_datasets(name=name)


@ensure_client()
def create_dataset(name: str, uid_column_name: Optional[str] = None):
    return _client_instance.create_dataset(name=name, uid_column_name=uid_column_name)


@ensure_client()
def get_shardset(dataset_id: str, shardset_id: str):
    return _client_instance.get_shardset(dataset_id=dataset_id, shardset_id=shardset_id)


@ensure_client()
def create_shardset(
    dataset_id: str, location: str, columns: list[DatasetColumnOptions] = []
):
    return _client_instance.create_shardset(
        dataset_id=dataset_id, location=location, columns=columns
    )


@ensure_client()
def sync_shardset(dataset_id: str, shardset_id: str, overwrite: bool = False):
    return _client_instance.sync_shardset(
        dataset_id=dataset_id, shardset_id=shardset_id, overwrite=overwrite
    )


@ensure_client()
def get_sync_shardset_status(dataset_id: str, shardset_id: str):
    return _client_instance.get_sync_shardset_status(
        dataset_id=dataset_id, shardset_id=shardset_id
    )


@ensure_client()
def create_iteration(
    dataset_id: str,
    shardsets: Optional[list[str]] = None,
    shuffle: bool = False,
    shuffle_seed: Optional[int] = None,
    shuffle_block_size: Optional[int] = None,
    batch_size: Optional[int] = None,
    replication_pg: Optional[list[list[int]]] = None,
    filters: Optional[list[IterationFilter]] = None,
    preprocessors: Optional[list[IterationPreprocessor]] = None,
    collater: Optional[IterationCollater] = None,
    rank: int = 0,
    world_size: Optional[int] = None,
    wait_participant_threshold: Optional[float] = None,
    cluster_sync: bool = False,
):
    return _client_instance.create_iteration(
        dataset_id=dataset_id,
        shardsets=shardsets,
        shuffle=shuffle,
        shuffle_seed=shuffle_seed,
        shuffle_block_size=shuffle_block_size,
        batch_size=batch_size,
        replication_pg=replication_pg,
        filters=filters,
        preprocessors=preprocessors,
        collater=collater,
        rank=rank,
        world_size=world_size,
        wait_participant_threshold=wait_participant_threshold,
        cluster_sync=cluster_sync,
    )


@ensure_client()
def get_iterations(
    dataset_id: Optional[str] = None, dataset_name: Optional[str] = None
):
    return _client_instance.get_iterations(
        dataset_id=dataset_id, dataset_name=dataset_name
    )


@ensure_client()
def get_iteration(iteration_id: str):
    return _client_instance.get_iteration(iteration_id=iteration_id)


@ensure_client()
def get_next_item(
    iteration_id: str,
    rank: int = 0,
    no_cache: bool = False,
):
    return _client_instance.get_next_item(
        iteration_id=iteration_id,
        rank=rank,
        no_cache=no_cache,
    )


@ensure_client()
def submit_next_item(
    iteration_id: str,
    rank: int = 0,
    no_cache: bool = False,
):
    return _client_instance.submit_next_item(
        iteration_id=iteration_id, rank=rank, no_cache=no_cache
    )


@ensure_client()
def get_submitted_result(iteration_id: str, cache_key: str):
    return _client_instance.get_submitted_result(
        iteration_id=iteration_id, cache_key=cache_key
    )


@ensure_client()
def complete_index(iteration_id: str, index: int):
    return _client_instance.complete_index(iteration_id=iteration_id, index=index)


@ensure_client()
def pushback(iteration_id: str):
    return _client_instance.pushback(iteration_id=iteration_id)


@ensure_client()
def get_progress(iteration_id: str):
    return _client_instance.get_progress(iteration_id=iteration_id)


@ensure_client()
def get_node_statuses():
    return _client_instance.get_node_statuses()
