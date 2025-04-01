import os
import shutil
import argparse
import subprocess
from uvicorn import run
import select
from threading import Event, Thread

from lavender_data.logging import get_logger
from dotenv import load_dotenv

load_dotenv()


def start_ui(ui_ready_event: Event, api_url: str, ui_port: int):
    logger = get_logger("lavender-data.server.ui")

    node_path = shutil.which("node")
    npm_path = shutil.which("npm")
    if node_path is None:
        logger.warning("node is not installed, cannot start UI")
        ui_ready_event.set()
        return

    if npm_path is None:
        logger.warning("npm is not installed, cannot start UI")
        ui_ready_event.set()
        return

    ui_dir = os.path.join(
        os.path.dirname(__file__), "..", "ui", "packages", "lavender-data-ui"
    )

    output = subprocess.run(
        [npm_path, "install", "--omit=dev"],
        cwd=ui_dir,
        check=True,
        capture_output=True,
    )
    logger.info(output.stdout.decode())

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

    while process.poll() is None:
        read_fds, _, _ = select.select([process.stdout, process.stderr], [], [], 1)
        for fd in read_fds:
            line = fd.readline().decode().strip()
            if "Ready" in line:
                ui_ready_event.set()
            logger.info(line)


def start_ui_and_wait_for_ready(api_url: str, ui_port: int):
    ui_ready_event = Event()
    ui_thread = Thread(
        target=start_ui,
        args=(ui_ready_event, api_url, ui_port),
    )
    ui_thread.start()
    ui_ready_event.wait()
    return ui_thread


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--ui-port", type=int, default=3000)

    args = parser.parse_args()

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
