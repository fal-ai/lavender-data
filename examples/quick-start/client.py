from lavender_data.client import api as lavender, Iteration

lavender.init(api_url="http://localhost:8000")

for data in Iteration.from_dataset(
    dataset_name="test-dataset",
    preprocessors=["append_new_column"],
    filters=[("uid_mod", {"mod": 2})],
    collater="pylist",
):
    print(data)
