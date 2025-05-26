import shutil
import select
import subprocess
import threading
import time
import httpx
import socket
import random

_threads = {}


def _flush_logs(server_process: subprocess.Popen):
    while server_process.poll() is None:
        read_fds, _, _ = select.select(
            [server_process.stdout, server_process.stderr], [], [], 1
        )
        for fd in read_fds:
            fd.read()

    server_process.stdout.close()
    server_process.stderr.close()


def get_free_port(min_port=1024, max_port=65535):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            port = random.randint(min_port, max_port)
            sock.bind(("", port))
            sock.close()
            return port
        except OSError:
            port += 1
    raise IOError("no free ports")


def start_server(port: int, env: dict):
    poetry = shutil.which("poetry")
    if poetry is None:
        raise Exception("poetry not found")

    server_process = subprocess.Popen(
        [
            poetry,
            "run",
            "lavender-data",
            "server",
            "run",
            "--init",
        ],
        env={
            **env,
            "LAVENDER_DATA_DISABLE_UI": "true",
            "LAVENDER_DATA_PORT": str(port),
            "LAVENDER_DATA_LOG_FILE": "./test.log",
            "LAVENDER_DATA_LOG_LEVEL": "DEBUG",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    _threads[server_process] = threading.Thread(
        target=_flush_logs, args=(server_process,), daemon=True
    )
    _threads[server_process].start()

    return server_process


def port_open(port: int):
    try:
        httpx.get(f"http://localhost:{port}/version")
        return True
    except httpx.ConnectError:
        return False


def wait_server_ready(server_process: subprocess.Popen, port: int, timeout: int = 30):
    start_time = time.time()
    while True:
        if port_open(port):
            break

        if not server_process.poll() is None:
            raise RuntimeError("Server process terminated.")

        if time.time() - start_time > timeout:
            raise TimeoutError("Server did not start in time.")

        time.sleep(0.1)


def stop_server(server_process: subprocess.Popen):
    server_process.terminate()
    server_process.wait(timeout=10)
