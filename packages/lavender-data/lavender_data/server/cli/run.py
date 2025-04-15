import os
import shutil
import subprocess
import uvicorn
import select
from threading import Event, Thread

from lavender_data.logging import get_logger
from dotenv import load_dotenv


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
        os.path.dirname(__file__), "..", "..", "ui", "packages", "lavender-data-ui"
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


def run(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: int = 1,
    disable_ui: bool = False,
    ui_port: int = 3000,
):
    load_dotenv()

    if not disable_ui:
        start_ui_and_wait_for_ready(f"http://{host}:{ui_port}", ui_port)

    uvicorn.run(
        "lavender_data.server:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
    )
