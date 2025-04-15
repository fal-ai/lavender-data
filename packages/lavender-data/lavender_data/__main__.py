import argparse
from lavender_data.client.cli import ClientCLI
from lavender_data.server.cli import ServerCLI


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="package")

    client_parser = subparsers.add_parser("client")
    client_cli = ClientCLI(client_parser)

    server_parser = subparsers.add_parser("server")
    server_cli = ServerCLI(server_parser)

    args = parser.parse_args()
    if args.package == "client":
        client_cli.main(args)
    elif args.package == "server":
        server_cli.main(args)
    else:
        parser.print_help()
        exit(1)


if __name__ == "__main__":
    main()
