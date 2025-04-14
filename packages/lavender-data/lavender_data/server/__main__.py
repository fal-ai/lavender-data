import os
import shutil
import argparse
import subprocess
from uvicorn import run
import select
from threading import Event, Thread

from lavender_data.server.scripts.create_api_key import create_api_key
from lavender_data.logging import get_logger
from dotenv import load_dotenv

load_dotenv()


def _read_process_output(process: subprocess.Popen):
    while process.poll() is None:
        read_fds, _, _ = select.select([process.stdout, process.stderr], [], [], 1)
        for fd in read_fds:
            yield fd.readline().decode().strip()


def _start_ui(ui_ready_event: Event, api_url: str, ui_port: int):
    logger = get_logger("lavender-data.server.ui")

    node_path = shutil.which("node")
    npm_path = shutil.which("npm")
    if node_path is None or npm_path is None:
        logger.warning(
            "Node is not installed, cannot start UI. Please refer to https://nodejs.org/download for installation instructions."
        )
        ui_ready_event.set()
        return

    ui_dir = os.path.join(
        os.path.dirname(__file__), "..", "ui", "packages", "lavender-data-ui"
    )

    logger.info("Installing UI dependencies")
    output = subprocess.Popen(
        [npm_path, "install", "--omit=dev"],
        cwd=ui_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for line in _read_process_output(output):
        logger.info(line)

    logger.info("Starting UI")
    process = subprocess.Popen(
        [node_path, "server.js"],
        cwd=ui_dir,
        env={
            "NEXT_PUBLIC_API_URL": api_url,
            "PORT": str(ui_port),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    for line in _read_process_output(process):
        logger.info(line)
        if "Ready" in line:
            ui_ready_event.set()


def start_ui_and_wait_for_ready(api_url: str, ui_port: int):
    ui_ready_event = Event()
    ui_thread = Thread(
        target=_start_ui,
        args=(ui_ready_event, api_url, ui_port),
    )
    ui_thread.start()
    ui_ready_event.wait()
    return ui_thread


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    # run
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--host", type=str, default="0.0.0.0")
    run_parser.add_argument("--port", type=int, default=8000)
    run_parser.add_argument("--reload", action="store_true")
    run_parser.add_argument("--workers", type=int, default=1)

    run_parser.add_argument("--disable-ui", action="store_true")
    run_parser.add_argument("--ui-port", type=int, default=3000)

    # run_parser.add_argument("--disable-auth", action="store_true")

    # create-api-key
    create_api_key_parser = subparsers.add_parser("create-api-key")
    create_api_key_parser.add_argument("--note", type=str, required=True)
    create_api_key_parser.add_argument("--expires-at", type=str, default=None)

    args = parser.parse_args()

    if args.command == "create-api-key":
        api_key = create_api_key(
            note=args.note,
            expires_at=args.expires_at,
        )
        print(f"{api_key.id}:{api_key.secret}")
        exit(0)

    elif args.command == "run":
        if not args.disable_ui:
            ui_thread = start_ui_and_wait_for_ready(
                f"http://{args.host}:{args.port}", args.ui_port
            )

        run(
            "lavender_data.server:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers,
        )

    else:
        parser.print_help()
        exit(1)
