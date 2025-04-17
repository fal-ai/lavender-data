import os
import shutil
import subprocess
import select
from threading import Event, Thread

from lavender_data.logging import get_logger


def _read_process_output(process: subprocess.Popen):
    while process.poll() is None:
        read_fds, _, _ = select.select([process.stdout, process.stderr], [], [], 1)
        for fd in read_fds:
            yield fd.readline().decode().strip()


def _start_ui(ui_done_event: Event, ui_failed_event: Event, api_url: str, ui_port: int):
    logger = get_logger("lavender-data.server.ui")

    node_path = shutil.which("node")
    npm_path = shutil.which("npm")
    if node_path is None or npm_path is None:
        logger.warning(
            "Node is not installed, cannot start UI. Please refer to https://nodejs.org/download for installation instructions."
        )
        ui_failed_event.set()
        ui_done_event.set()
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
            "API_URL": api_url,
            "PORT": str(ui_port),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    for line in _read_process_output(process):
        logger.info(line)
        if "Ready" in line:
            ui_done_event.set()

    ui_failed_event.set()
    ui_done_event.set()


def setup_ui(api_url: str, ui_port: int):
    ui_done_event = Event()
    ui_failed_event = Event()
    ui_thread = Thread(
        target=_start_ui,
        args=(ui_done_event, ui_failed_event, api_url, ui_port),
    )
    ui_thread.start()
    ui_done_event.wait()
    if ui_failed_event.is_set():
        raise RuntimeError("UI failed to start")
    return ui_thread
