# Lavender Data

## Key Features

### Streaming

- **Remote Preprocessing**: Preprocess data on a remote server to offload your GPUs while training
- **Zero Disk Usage**: All data is loaded directly into memory through a network
- **Cloud Storage Support**: Load data from cloud storages

### Joinable Dataset

- **Efficient Feature Addition**: Add new features to your dataset without rewriting your data
- **Efficient Data Loading**: Selectively load only the features you need for your task

### Flexible Iteration

- **Online Filtering**: Filter data on the fly using custom filters
- **Shuffle**: Shuffle data across shards
- **Resumable**: Resume an iteration from where you left off
- **Fault Tolerant**: Retry or skip failed samples without any concerns

### Web UI

### Customizable

- **Custom Modules**: Easily define custom filters, collaters, and preprocessors

## Key Concepts

### Dataset Layers

<img src="./assets/dataset-layers.png" alt="Dataset Layers" />

- **Dataset**: The top-level container for your data, identified by a unique name
- **Shardset**: A collection of data shards within a dataset, typically representing a group of related columns
- **Shard**: A single file that contains a subset of the data.

### Pipeline Overview

<img src="./assets/overview.png" alt="Pipeline Overview" />

- **Filters**: Determine which samples to include/exclude during iteration
- **Collaters**: Control how individual samples are combined into batches
- **Preprocessors**: Transform batches before they're returned to your application

## Basic Usage

### Installation

```bash
pip install lavender-data
```

### Starting the Server

```bash
python3 -m lavender_data.server --port 8000 --host 0.0.0.0
```

### Initializing the Client

```python
from lavender_data.client import api as lavender

lavender.init(api_url="http://localhost:8000")
```

### Creating a Dataset

```python
# Create a dataset
from lavender_data.client import api as lavender

dataset = lavender.create_dataset(name="my-dataset", uid_column_name="uid")

# Add a shardset with columns
shardset = lavender.create_shardset(
    dataset_id=dataset.id,
    location="file://.cache/lavender-data/my_shards",
    columns=[
        lavender.DatasetColumnOptions(
            name="uid",
            description="Unique identifier",
            type_="int",
        ),
        lavender.DatasetColumnOptions(
            name="text",
            description="Text content",
            type_="str",
        ),
    ],
)
```

### Writing Data

```python
# Write data to the shardset
from lavender_data.shard import Writer

writer = Writer.get(
    format="csv",
    dataset_id=dataset.id,
    shardset_id=shardset.id,
)

# Write samples
samples = [
    {"uid": i, "text": f"Sample {i}"} for i in range(100)
]
writer.write(samples=samples, shard_index=0)
```

### Iterating over data

```python
from lavender_data.client import Iteration

dataset = lavender.get_dataset(name="my-dataset")
shardset = dataset.shardsets[0] # Select the shardset you want to iterate over

iteration = Iteration.from_dataset(
    dataset_id=dataset.id,
    shardsets=[shardset.id],
    batch_size=10,
    shuffle=True,
)

for batch in iteration:
    # Process your data
    print(batch)
```

### Custom Modules

Create a module directory and set the environment variable:

```bash
export LAVENDER_DATA_MODULES_DIR=./modules
```

Define custom components:

```python
# modules/custom_filter.py
from lavender_data.server import FilterRegistry, Filter

@FilterRegistry.register("only_even_uids")
class OnlyEvenUidsFilter(Filter):
    def filter(self, sample: dict) -> bool:
        return sample["uid"] % 2 == 0

# Use it in your iteration
iteration = Iteration.from_config(
    IterationConfig(
        dataset_id=dataset.id,
        shardsets=[shardset.id],
        filter="only_even_uids",
    )
)
```

Refer to the [example](https://github.com/fal-ai/lavender-data/tree/main/examples/quick-start/quick-start.ipynb) for more details.

## Web UI

### Installation

Using docker:

```bash
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://localhost:8000 lavender-data-ui
```
