import os
import shutil
import select
import subprocess
import time


def flush_logs(server_process: subprocess.Popen):
    if server_process.poll() is not None:
        return

    read_fds, _, _ = select.select(
        [server_process.stdout, server_process.stderr], [], [], 1
    )
    for fd in read_fds:
        fd.read()


def start_server(port: int, env_file: str, timeout: int = 10):
    server_process = subprocess.Popen(
        [
            "lavender-data",
            "server",
            "run",
            "--disable-ui",
            "--port",
            str(port),
            "--env-file",
            env_file,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

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

    print(
        f"Server started with env {env_file} on {port} in {time.time() - start_time} seconds"
    )
    return server_process


def stop_server(server_process: subprocess.Popen):
    try:
        server_process.terminate()
    except Exception as e:
        print(f"Error stopping server: {e}")


if __name__ == "__main__":
    logs_dir = "./logs"
    shutil.rmtree(logs_dir, ignore_errors=True)
    os.makedirs(logs_dir, exist_ok=True)

    head = start_server(8000, ".env.head")
    node_1 = start_server(8001, ".env.node.1")
    node_2 = start_server(8002, ".env.node.2")

    try:
        while True:
            flush_logs(head)
            flush_logs(node_1)
            flush_logs(node_2)
    except KeyboardInterrupt:
        print("Aborting...")
        pass

    stop_server(head)
    stop_server(node_1)
    stop_server(node_2)
