import os
import shutil
import subprocess
import select
from lavender_data.logging import get_logger


def _read_process_output(process: subprocess.Popen):
    while process.poll() is None:
        read_fds, _, _ = select.select([process.stdout, process.stderr], [], [], 1)
        for fd in read_fds:
            yield fd.readline().decode().strip()


def _start_ui(api_url: str, ui_port: int):
    logger = get_logger("lavender-data.server.ui")

    node_path = shutil.which("node")
    npm_path = shutil.which("npm")
    if node_path is None or npm_path is None:
        raise RuntimeError(
            "Node is not installed, cannot start UI. Please refer to https://nodejs.org/download for installation instructions."
        )

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
            return process

    raise RuntimeError("UI failed to start")


def setup_ui(api_url: str, ui_port: int):
    process = _start_ui(api_url=api_url, ui_port=ui_port)
    return process
