from lavender_data.client import LavenderDataClient
from lavender_data.serialize import deserialize_sample


def _api(api_url: str, api_key: str):
    return LavenderDataClient(api_url=api_url, api_key=api_key)


def get_version(api_url: str, api_key: str):
    return _api(api_url=api_url, api_key=api_key).get_version()


def get_datasets(api_url: str, api_key: str, name: str):
    return _api(api_url=api_url, api_key=api_key).get_datasets(name=name)


def get_dataset(api_url: str, api_key: str, dataset_id: str, name: str):
    return _api(api_url=api_url, api_key=api_key).get_dataset(
        dataset_id=dataset_id, name=name
    )


def create_dataset(
    api_url: str, api_key: str, name: str, uid_column_name: str, shardset_location: str
):
    return _api(api_url=api_url, api_key=api_key).create_dataset(
        name=name, uid_column_name=uid_column_name, shardset_location=shardset_location
    )


def delete_dataset(api_url: str, api_key: str, dataset_id: str):
    return _api(api_url=api_url, api_key=api_key).delete_dataset(dataset_id=dataset_id)


def get_shardset(api_url: str, api_key: str, dataset_id: str, shardset_id: str):
    return _api(api_url=api_url, api_key=api_key).get_shardset(
        dataset_id=dataset_id, shardset_id=shardset_id
    )


def create_shardset(api_url: str, api_key: str, dataset_id: str, location: str):
    return _api(api_url=api_url, api_key=api_key).create_shardset(
        dataset_id=dataset_id, location=location, columns=[]
    )


def delete_shardset(api_url: str, api_key: str, dataset_id: str, shardset_id: str):
    return _api(api_url=api_url, api_key=api_key).delete_shardset(
        dataset_id=dataset_id, shardset_id=shardset_id
    )


def sync_shardset(
    api_url: str, api_key: str, dataset_id: str, shardset_id: str, overwrite: bool
):
    return _api(api_url=api_url, api_key=api_key).sync_shardset(
        dataset_id=dataset_id, shardset_id=shardset_id, overwrite=overwrite
    )


def get_iterations(api_url: str, api_key: str, dataset_id: str, dataset_name: str):
    return _api(api_url=api_url, api_key=api_key).get_iterations(
        dataset_id=dataset_id, dataset_name=dataset_name
    )


def get_iteration(api_url: str, api_key: str, iteration_id: str):
    return _api(api_url=api_url, api_key=api_key).get_iteration(
        iteration_id=iteration_id
    )


def get_next_item(
    api_url: str,
    api_key: str,
    iteration_id: str,
    rank: int,
    no_cache: bool,
    max_retry_count: int,
):
    return deserialize_sample(
        _api(api_url=api_url, api_key=api_key).get_next_item(
            iteration_id=iteration_id,
            rank=rank,
            no_cache=no_cache,
            max_retry_count=max_retry_count,
        )[0]
    )


def submit_next_item(
    api_url: str,
    api_key: str,
    iteration_id: str,
    rank: int,
    no_cache: bool,
    max_retry_count: int,
):
    return _api(api_url=api_url, api_key=api_key).submit_next_item(
        iteration_id=iteration_id,
        rank=rank,
        no_cache=no_cache,
        max_retry_count=max_retry_count,
    )


def get_submitted_result(api_url: str, api_key: str, iteration_id: str, cache_key: str):
    return deserialize_sample(
        _api(api_url=api_url, api_key=api_key).get_submitted_result(
            iteration_id=iteration_id, cache_key=cache_key
        )[0]
    )


def get_progress(api_url: str, api_key: str, iteration_id: str):
    return _api(api_url=api_url, api_key=api_key).get_progress(
        iteration_id=iteration_id
    )


def complete_index(api_url: str, api_key: str, iteration_id: str, index: int):
    return _api(api_url=api_url, api_key=api_key).complete_index(
        iteration_id=iteration_id, index=index
    )


def pushback(api_url: str, api_key: str, iteration_id: str):
    return _api(api_url=api_url, api_key=api_key).pushback(iteration_id=iteration_id)
