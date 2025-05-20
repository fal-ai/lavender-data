import argparse
import json
from typing import Optional

from .api_call import (
    get_version,
    get_datasets,
    get_dataset,
    create_dataset,
    delete_dataset,
    get_shardset,
    create_shardset,
    delete_shardset,
    sync_shardset,
    get_iterations,
    get_iteration,
    get_next_item,
    submit_next_item,
    get_submitted_result,
    complete_index,
    pushback,
    get_progress,
)


class ClientCLI:
    def __init__(self, parent_parser: Optional[argparse.ArgumentParser] = None):
        self.parser = (
            argparse.ArgumentParser() if parent_parser is None else parent_parser
        )
        self.parser.add_argument("--api-url", type=str, default="http://localhost:8000")
        self.parser.add_argument("--api-key", type=str, default=None)
        subparsers = self.parser.add_subparsers(dest="resource")

        self.version_parser = subparsers.add_parser("version")

        self.datasets_parser = subparsers.add_parser("datasets")
        self.datasets_command_parser = self.datasets_parser.add_subparsers(
            dest="command"
        )
        self.datasets_list = self.datasets_command_parser.add_parser("list")
        self.datasets_list.add_argument("--name", type=str, default=None)

        self.datasets_get = self.datasets_command_parser.add_parser("get")
        self.datasets_get.add_argument("--id", type=str)
        self.datasets_get.add_argument("--name", type=str)

        self.datasets_create = self.datasets_command_parser.add_parser("create")
        self.datasets_create.add_argument("--name", type=str, required=True)
        self.datasets_create.add_argument("--uid-column-name", type=str, required=True)
        self.datasets_create.add_argument(
            "--shardset-location", type=str, required=False, default=None
        )
        self.datasets_delete = self.datasets_command_parser.add_parser("delete")
        self.datasets_delete.add_argument("--id", type=str, required=True)

        self.shardsets_parser = subparsers.add_parser("shardsets")
        self.shardsets_command_parser = self.shardsets_parser.add_subparsers(
            dest="command"
        )
        self.shardsets_get = self.shardsets_command_parser.add_parser("get")
        self.shardsets_get.add_argument("--dataset-id", type=str, required=True)
        self.shardsets_get.add_argument("--shardset-id", type=str, required=True)

        self.shardsets_create = self.shardsets_command_parser.add_parser("create")
        self.shardsets_create.add_argument("--dataset-id", type=str, required=True)
        self.shardsets_create.add_argument("--location", type=str, required=True)

        self.shardsets_delete = self.shardsets_command_parser.add_parser("delete")
        self.shardsets_delete.add_argument("--dataset-id", type=str, required=True)
        self.shardsets_delete.add_argument("--shardset-id", type=str, required=True)

        self.shardsets_sync = self.shardsets_command_parser.add_parser("sync")
        self.shardsets_sync.add_argument("--dataset-id", type=str, required=True)
        self.shardsets_sync.add_argument("--shardset-id", type=str, required=True)
        self.shardsets_sync.add_argument("--overwrite", action="store_true")

        self.iterations_parser = subparsers.add_parser("iterations")
        self.iterations_command_parser = self.iterations_parser.add_subparsers(
            dest="command"
        )
        self.iterations_list = self.iterations_command_parser.add_parser("list")
        self.iterations_list.add_argument("--dataset-id", type=str, default=None)
        self.iterations_list.add_argument("--dataset-name", type=str, default=None)

        self.iterations_get = self.iterations_command_parser.add_parser("get")
        self.iterations_get.add_argument("id", type=str)

        self.iterations_next = self.iterations_command_parser.add_parser("next")
        self.iterations_next.add_argument("id", type=str)
        self.iterations_next.add_argument("--rank", type=int, default=0)
        self.iterations_next.add_argument("--no-cache", action="store_true")
        self.iterations_next.add_argument("--max-retry-count", type=int, default=0)

        self.iterations_submit_next_item = self.iterations_command_parser.add_parser(
            "async-next"
        )
        self.iterations_submit_next_item.add_argument("id", type=str)
        self.iterations_submit_next_item.add_argument("--rank", type=int, default=0)
        self.iterations_submit_next_item.add_argument("--no-cache", action="store_true")
        self.iterations_submit_next_item.add_argument(
            "--max-retry-count", type=int, default=0
        )

        self.iterations_async_result = self.iterations_command_parser.add_parser(
            "async-result"
        )
        self.iterations_async_result.add_argument("id", type=str)
        self.iterations_async_result.add_argument("key", type=str)

        self.iterations_complete_index = self.iterations_command_parser.add_parser(
            "complete-index"
        )
        self.iterations_complete_index.add_argument("id", type=str)
        self.iterations_complete_index.add_argument("index", type=int)

        self.iterations_pushback = self.iterations_command_parser.add_parser("pushback")
        self.iterations_pushback.add_argument("id", type=str)

        self.iterations_get_progress = self.iterations_command_parser.add_parser(
            "get-progress"
        )
        self.iterations_get_progress.add_argument("id", type=str)

    def get_parser(self):
        return self.parser

    def main(self, args: Optional[argparse.Namespace] = None):
        if args is None:
            args = self.parser.parse_args()

        if args.resource == "version":
            result = get_version(args.api_url, args.api_key).to_dict()
        elif args.resource == "datasets":
            if args.command == "list":
                result = [
                    d.to_dict()
                    for d in get_datasets(args.api_url, args.api_key, args.name)
                ]
            elif args.command == "create":
                result = create_dataset(
                    args.api_url,
                    args.api_key,
                    args.name,
                    args.uid_column_name,
                    args.shardset_location,
                ).to_dict()
            elif args.command == "delete":
                result = delete_dataset(args.api_url, args.api_key, args.id).to_dict()
            elif args.command == "get":
                result = get_dataset(
                    args.api_url, args.api_key, args.id, args.name
                ).to_dict()
            else:
                self.datasets_parser.print_help()
                exit(1)
        elif args.resource == "shardsets":
            if args.command == "get":
                result = get_shardset(
                    args.api_url, args.api_key, args.dataset_id, args.shardset_id
                ).to_dict()
            elif args.command == "create":
                result = create_shardset(
                    args.api_url, args.api_key, args.dataset_id, args.location
                ).to_dict()
            elif args.command == "delete":
                result = delete_shardset(
                    args.api_url, args.api_key, args.dataset_id, args.shardset_id
                ).to_dict()
            elif args.command == "sync":
                result = sync_shardset(
                    args.api_url,
                    args.api_key,
                    args.dataset_id,
                    args.shardset_id,
                    args.overwrite,
                ).to_dict()
            else:
                self.shardsets_parser.print_help()
                exit(1)
        elif args.resource == "iterations":
            if args.command == "list":
                result = [
                    d.to_dict()
                    for d in get_iterations(
                        args.api_url, args.api_key, args.dataset_id, args.dataset_name
                    )
                ]
            elif args.command == "get":
                result = get_iteration(args.api_url, args.api_key, args.id).to_dict()
            elif args.command == "next":
                result = get_next_item(
                    args.api_url,
                    args.api_key,
                    args.id,
                    args.rank,
                    args.no_cache,
                    args.max_retry_count,
                )
            elif args.command == "async-next":
                result = submit_next_item(
                    args.api_url,
                    args.api_key,
                    args.id,
                    args.rank,
                    args.no_cache,
                    args.max_retry_count,
                )
            elif args.command == "async-result":
                result = get_submitted_result(
                    args.api_url, args.api_key, args.id, args.key
                )
            elif args.command == "complete-index":
                result = complete_index(args.api_url, args.api_key, args.id, args.index)
            elif args.command == "pushback":
                result = pushback(args.api_url, args.api_key, args.id)
            elif args.command == "get-progress":
                result = get_progress(args.api_url, args.api_key, args.id).to_dict()
            else:
                self.iterations_parser.print_help()
                exit(1)
        else:
            self.parser.print_help()
            exit(1)

        if isinstance(result, list):
            for r in result:
                print(json.dumps(r))
        else:
            print(json.dumps(result, indent=2))
