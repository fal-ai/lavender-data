.PHONY: openapi-python-client ui

all: openapi-python-client ui

openapi-python-client:
	openapi-python-client generate --url http://localhost:8000/openapi.json --config openapi.config.yaml --overwrite
	sed -i -e 's/response_200 = File(payload=BytesIO(response.json()))/response_200 = File(payload=BytesIO(response.content))/g' openapi-lavender-data-rest/openapi_lavender_data_rest/api/iterations/get_next_iterations_iteration_id_next_get.py
	sed -i -e 's/response_200 = File(payload=BytesIO(response.json()))/response_200 = File(payload=BytesIO(response.content))/g' openapi-lavender-data-rest/openapi_lavender_data_rest/api/iterations/get_submitted_result_iterations_iteration_id_next_cache_key_get.py
	rm openapi-lavender-data-rest/openapi_lavender_data_rest/api/iterations/get_next_iterations_iteration_id_next_get.py-e 2> /dev/null
	rm openapi-lavender-data-rest/openapi_lavender_data_rest/api/iterations/get_submitted_result_iterations_iteration_id_next_cache_key_get.py-e 2> /dev/null
ui:
	cd ./ui && pnpm build && cd ../
	cp -r ./ui/.next/standalone/ui/ lavender_data/ui/
	rm -rf ./ui/.next/node_modules
