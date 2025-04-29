import os
from dotenv import load_dotenv

import lavender_data.client as lavender

load_dotenv()

lavender.init(
    api_url="http://localhost:8000",
    api_key=os.getenv("LAVENDER_DATA_API_KEY"),
)

if __name__ == "__main__":
    for data in lavender.LavenderDataLoader(
        dataset_name="test-dataset",
        preprocessors=["append_new_column"],
        filters=[("uid_mod", {"mod": 10})],
        collater="pylist",
        no_cache=True,
    ).torch(
        prefetch_factor=2,
        in_order=True,
    ):
        print(data)
