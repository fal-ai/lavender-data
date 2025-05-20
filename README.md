<p align="center">
    <img src="https://github.com/fal-ai/lavender-data/raw/main/assets/logo.webp" alt="Lavender Data Logo" width="50%" />
</p>

<h2>
    <p align="center">
        Load & evolve datasets efficiently
    </p>
</h2>

<p align="center">
    <a href="https://pypi.org/project/lavender-data/">
        <img alt="PyPI" src="https://img.shields.io/pypi/v/lavender-data.svg">
    </a>
    <a href="https://discord.gg/fal-ai">
        <img alt="Discord" src="https://img.shields.io/badge/Discord-chat-2eb67d.svg?logo=discord">
    </a>
    <a href="https://github.com/fal-ai/lavender-data/blob/main/LICENSE">
        <img alt="License" src="https://img.shields.io/badge/License-Apache%202.0-green.svg">
    </a>
</p>

<br />

<p align="center">
    Please visit our docs for more information.
    <br />
    <a href="https://docs.lavenderdata.com/">
        docs.lavenderdata.com
    </a>
</p>

## Quick Start

### Installation

```bash
pip install lavender-data
```

#### Start the server

```bash
lavender-data server start --init
```

```
lavender-data is running on 0.0.0.0:8000
UI is running on http://localhost:3000
API key created: la-...
```

Save the API key to use it in the next steps.

```bash
export LAVENDER_API_URL=http://0.0.0.0:8000
export LAVENDER_API_KEY=la-...
```

### Create an example dataset

```bash
lavender-data client \
  datasets create \
  --name my_dataset \
  --uid-column-name id \
  --shardset-location https://docs.lavenderdata.com/example-dataset/images/
```

### Iterate over the dataset

```python
import lavender_data.client as lavender

lavender.init()

iteration = lavender.LavenderDataLoader(
    dataset_name="my_dataset",
    shuffle=True,
    shuffle_block_size=10,
)

for i in iteration:
    print(i["id"])
```

<p align="center">
    Please visit our docs for more information.
    <br />
    <a href="https://docs.lavenderdata.com/">
        docs.lavenderdata.com
    </a>
</p>
