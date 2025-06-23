from lavender_data.server.db.models import Shardset


def get_main_shardset(shardsets: list[Shardset]) -> Shardset:
    """Pick the main shardset for getting samples from.
    During the iteration, the samples are yielded as the order of the samples in the main shardset.

    The main shardset is configured by the user.
    If there is no main shardset, the one with the oldest creation date is picked.
    """
    main_shardset = next((shardset for shardset in shardsets if shardset.is_main), None)
    if main_shardset is not None:
        return main_shardset

    # If there is no main shardset, pick the oldest one.
    oldest_shardset = min(shardsets, key=lambda x: x.created_at)
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
