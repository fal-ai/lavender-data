from contextlib import contextmanager
from typing import Iterator
from lavender_data.client import api


@contextmanager
def init(api_url: str, api_key: str) -> Iterator[api.LavenderDataClient]:
    api.init(api_url=api_url, api_key=api_key)
    yield api


def get_version(api_url: str, api_key: str):
    with init(api_url=api_url, api_key=api_key):
        return api.get_version()


def get_datasets(api_url: str, api_key: str, name: str):
    with init(api_url=api_url, api_key=api_key):
        return api.get_datasets(name=name)


def get_dataset(api_url: str, api_key: str, dataset_id: str, name: str):
    with init(api_url=api_url, api_key=api_key):
        return api.get_dataset(dataset_id=dataset_id, name=name)


def create_dataset(api_url: str, api_key: str, name: str, uid_column_name: str):
    with init(api_url=api_url, api_key=api_key):
        return api.create_dataset(name=name, uid_column_name=uid_column_name)


def get_shardset(api_url: str, api_key: str, dataset_id: str, shardset_id: str):
    with init(api_url=api_url, api_key=api_key):
        return api.get_shardset(dataset_id=dataset_id, shardset_id=shardset_id)


def create_shardset(api_url: str, api_key: str, dataset_id: str, location: str):
    with init(api_url=api_url, api_key=api_key):
        return api.create_shardset(dataset_id=dataset_id, location=location, columns=[])


def create_shard(
    api_url: str,
    api_key: str,
    dataset_id: str,
    shardset_id: str,
    location: str,
    filesize: int,
    samples: int,
    format: str,
    index: int,
    overwrite: bool,
):
    with init(api_url=api_url, api_key=api_key):
        return api.create_shard(
            dataset_id=dataset_id,
            shardset_id=shardset_id,
            location=location,
            filesize=filesize,
            samples=samples,
            format=format,
            index=index,
            overwrite=overwrite,
        )


def get_iterations(api_url: str, api_key: str, dataset_id: str, dataset_name: str):
    with init(api_url=api_url, api_key=api_key):
        return api.get_iterations(dataset_id=dataset_id, dataset_name=dataset_name)


def get_iteration(api_url: str, api_key: str, iteration_id: str):
    with init(api_url=api_url, api_key=api_key):
        return api.get_iteration(iteration_id=iteration_id)


def get_next_item(
    api_url: str,
    api_key: str,
    iteration_id: str,
    rank: int,
    async_mode: bool,
    no_cache: bool,
):
    with init(api_url=api_url, api_key=api_key):
        return api.get_next_item(
            iteration_id=iteration_id,
            rank=rank,
            async_mode=async_mode,
            no_cache=no_cache,
        )


def get_next_item_async_result(
    api_url: str, api_key: str, iteration_id: str, cache_key: str
):
    with init(api_url=api_url, api_key=api_key):
        return api.get_next_item_async_result(
            iteration_id=iteration_id, cache_key=cache_key
        )


def get_progress(api_url: str, api_key: str, iteration_id: str):
    with init(api_url=api_url, api_key=api_key):
        return api.get_progress(iteration_id=iteration_id)


def complete_index(api_url: str, api_key: str, iteration_id: str, index: int):
    with init(api_url=api_url, api_key=api_key):
        return api.complete_index(iteration_id=iteration_id, index=index)


def pushback(api_url: str, api_key: str, iteration_id: str):
    with init(api_url=api_url, api_key=api_key):
        return api.pushback(iteration_id=iteration_id)
