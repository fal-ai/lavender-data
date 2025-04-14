from lavender_data.client import api as lavender
from lavender_data.shard import Writer


lavender.init(api_url="http://localhost:8000")

dataset = lavender.get_dataset(name="test-dataset")
shardset = dataset.shardsets[0]

print(dataset.id, shardset.id)
writer = Writer.get(
    format="csv",
    dataset_id=dataset.id,
    shardset_id=shardset.id,
    persist_files=True,
)

shard_count = 10
samples_per_shard = 10

for shard_index in range(shard_count):
    samples = [
        {
            "text": f"Sample {i + shard_index * samples_per_shard}",
            "uid": i + shard_index * samples_per_shard,
        }
        for i in range(samples_per_shard)
    ]
    writer.write(
        samples=samples,
        shard_index=shard_index,
        overwrite=True,
    )
