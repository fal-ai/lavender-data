import argparse
from typing import Optional

from .run import run
from .create_api_key import create_api_key
from .daemon import start, stop, restart, logs


class ServerCLI:
    def __init__(self, parent_parser: Optional[argparse.ArgumentParser] = None):
        self.parser = (
            argparse.ArgumentParser() if parent_parser is None else parent_parser
        )
        subparsers = self.parser.add_subparsers(dest="command")

        # create-api-key
        self.create_api_key_parser = subparsers.add_parser("create-api-key")
        self.create_api_key_parser.add_argument("--note", type=str, default=None)
        self.create_api_key_parser.add_argument("--expires-at", type=str, default=None)

        # run
        self.run_parser = subparsers.add_parser("run")
        self.run_parser.add_argument("--env-file", type=str, default=".env")

        # daemon
        self.start_parser = subparsers.add_parser("start")
        self.start_parser.add_argument("--init", action="store_true")
        self.start_parser.add_argument("--env-file", type=str, default=".env")

        self.stop_parser = subparsers.add_parser("stop")

        self.restart_parser = subparsers.add_parser("restart")
        self.restart_parser.add_argument("--env-file", type=str, default=".env")

        self.logs_parser = subparsers.add_parser("logs")
        self.logs_parser.add_argument("-f", action="store_true")
        self.logs_parser.add_argument("-n", type=int, default=10)

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
            run(env_file=args.env_file)

        elif args.command == "start":
            start(init=args.init, env_file=args.env_file)

        elif args.command == "stop":
            stop()

        elif args.command == "restart":
            restart(env_file=args.env_file)

        elif args.command == "logs":
            logs(f_flag=args.f, n_lines=args.n)

        else:
            self.parser.print_help()
            exit(1)
