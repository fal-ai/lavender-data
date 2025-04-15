import argparse
from typing import Optional

from .run import run
from .create_api_key import create_api_key


class ServerCLI:
    def __init__(self, parent_parser: Optional[argparse.ArgumentParser] = None):
        self.parser = (
            argparse.ArgumentParser() if parent_parser is None else parent_parser
        )
        subparsers = self.parser.add_subparsers(dest="command")

        # run
        self.run_parser = subparsers.add_parser("run")
        self.run_parser.add_argument("--host", type=str, default="0.0.0.0")
        self.run_parser.add_argument("--port", type=int, default=8000)
        self.run_parser.add_argument("--reload", action="store_true")
        self.run_parser.add_argument("--workers", type=int, default=1)
        self.run_parser.add_argument("--disable-ui", action="store_true")
        self.run_parser.add_argument("--ui-port", type=int, default=3000)

        # create-api-key
        self.create_api_key_parser = subparsers.add_parser("create-api-key")
        self.create_api_key_parser.add_argument("--note", type=str, required=True)
        self.create_api_key_parser.add_argument("--expires-at", type=str, default=None)

    def get_parser(self):
        return self.parser

    def main(self, args: Optional[argparse.Namespace] = None):
        if args is None:
            args = self.parser.parse_args()

        if args.command == "create-api-key":
            api_key = create_api_key(
                note=args.note,
                expires_at=args.expires_at,
            )
            print(f"{api_key.id}:{api_key.secret}")
            exit(0)

        elif args.command == "run":
            run(
                host=args.host,
                port=args.port,
                reload=args.reload,
                workers=args.workers,
                disable_ui=args.disable_ui,
                ui_port=args.ui_port,
            )

        else:
            self.parser.print_help()
            exit(1)
