from lavender_data.server.db import Shardset


def get_main_shardset(shardsets: list[Shardset]) -> Shardset:
    """Pick the main shardset for getting samples from.
    During the iteration, the samples are yielded as the order of the samples in the main shardset.

    The main shardset is the one with the most samples.
    If there are multiple shardsets with the same number of samples,
    the one with the oldest creation date is picked.
    """
    shardset_with_most_samples = None
    total_samples = shardsets[0].total_samples
    for shardset in shardsets:
        if total_samples < shardset.total_samples:
            shardset_with_most_samples = shardset
            total_samples = shardset.total_samples
    if shardset_with_most_samples is not None:
        return shardset_with_most_samples

    oldest_shardset = shardsets[0]
    oldest_shardset_created_at = shardsets[0].created_at
    for shardset in shardsets:
        if oldest_shardset_created_at > shardset.created_at:
            oldest_shardset_created_at = shardset.created_at
            oldest_shardset = shardset

    return oldest_shardset


def span(index: int, shard_samples: list[int]) -> tuple[int, int]:
    sample_index = index
    shard_index = 0
    for samples in shard_samples:
        if sample_index < samples:
            break
        else:
            sample_index -= samples
            shard_index += 1

    return (shard_index, sample_index)
