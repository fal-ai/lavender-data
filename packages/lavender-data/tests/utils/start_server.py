import shutil
import select
import subprocess
import threading
import time

_threads = {}


def _flush_logs(server_process: subprocess.Popen):
    while server_process.poll() is None:
        read_fds, _, _ = select.select(
            [server_process.stdout, server_process.stderr], [], [], 1
        )
        for fd in read_fds:
            fd.readline().decode().strip()

    server_process.stdout.close()
    server_process.stderr.close()


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
            "--disable-ui",
            "--port",
            str(port),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    return server_process


def wait_server_ready(server_process: subprocess.Popen, timeout: int = 10):
    server_ready = False
    start_time = time.time()
    while server_process.poll() is None and not server_ready:
        read_fds, _, _ = select.select(
            [server_process.stdout, server_process.stderr], [], [], 1
        )
        for fd in read_fds:
            line = fd.readline().decode().strip()
            if "Application startup complete." in line:
                server_ready = True

        if time.time() - start_time > timeout:
            raise TimeoutError("Server did not start in time.")

    _threads[server_process] = threading.Thread(
        target=_flush_logs, args=(server_process,), daemon=True
    )
    _threads[server_process].start()


def stop_server(server_process: subprocess.Popen):
    server_process.terminate()
    server_process.wait()
    _threads[server_process].join()
    del _threads[server_process]
