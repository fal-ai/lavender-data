from lavender_data.server.db import Shardset


def get_main_shardset(shardsets: list[Shardset]) -> Shardset:
    main_shardset = shardsets[0]
    total_samples = shardsets[0].total_samples
    for shardset in shardsets:
        if total_samples > shardset.total_samples:
            main_shardset = shardset
            total_samples = shardset.total_samples
    return main_shardset


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
