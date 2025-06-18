import os
import atexit
import signal
import select
import time
import httpx
import multiprocessing as mp
import daemon
from daemon.pidfile import PIDLockFile

from .run import run
from lavender_data.server.settings import get_settings, root_dir

PID_LOCK_FILE = "/tmp/lavender-data.pid"
LOG_FILE = os.path.join(root_dir, "server.terminal.log")
WORKING_DIRECTORY = root_dir

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


def _run(*args, **kwargs):
    import sys

    with open(LOG_FILE, "a") as f:
        sys.stdout = f
        sys.stderr = f
        run(*args, **kwargs)


def watch_log_file():
    head_read = False
    try:
        with open(LOG_FILE, "r") as f:
            while True:
                read_fds, _, _ = select.select([f], [], [], 1)
                for fd in read_fds:
                    if not head_read:
                        head_read = True
                        fd.read()
                        continue

                    yield fd.read()
    except KeyboardInterrupt:
        pass


def port_open(port: int):
    try:
        httpx.get(f"http://localhost:{port}/version")
        return True
    except httpx.ConnectError:
        return False


def start(*args, **kwargs):
    pid_lock_file = PIDLockFile(PID_LOCK_FILE)
    if pid_lock_file.is_locked():
        print("Server already running")
        exit(1)

    f = open(LOG_FILE, "a")
    f.write(
        "[%s] Starting lavender-data server...\n" % time.strftime("%Y-%m-%d %H:%M:%S")
    )
    f.flush()
    log_file_position = f.tell()

    ctx = mp.get_context("spawn")
    process = ctx.Process(target=_run, args=args, kwargs=kwargs)
    process.start()
    atexit.register(lambda: os.kill(process.pid, signal.SIGINT))

    settings = get_settings()

    timeout = 60
    start_time = time.time()
    while True:
        if port_open(settings.lavender_data_port):
            break

        if not process.is_alive():
            print(f"Failed to start server (check {LOG_FILE} for more details)")
            exit(1)

        if time.time() - start_time > timeout:
            print(
                f"Timeout waiting for server to start (check {LOG_FILE} for more details)"
            )
            exit(1)

        time.sleep(0.1)

    with open(LOG_FILE, "r") as f:
        f.seek(log_file_position)
        for line in f.readlines():
            if "API key created" in line:
                print(line, end="")

            if "UI is running" in line:
                print(
                    f"UI is running on http://localhost:{settings.lavender_data_ui_port}"
                )

            if "UI failed to start" in line:
                print(line.split("UI failed to start: ")[1], end="")

    print(
        f"lavender-data is running on http://{settings.lavender_data_host}:{settings.lavender_data_port}"
    )
    with daemon.DaemonContext(
        working_directory=WORKING_DIRECTORY,
        umask=0o002,
        pidfile=pid_lock_file,
    ):
        for line in watch_log_file():
            continue


def stop():
    pid_lock_file = PIDLockFile(PID_LOCK_FILE)
    if not pid_lock_file.is_locked():
        return

    pid = pid_lock_file.read_pid()
    os.kill(pid, signal.SIGTERM)


def restart(*args, **kwargs):
    stop()
    time.sleep(1)
    start(*args, **kwargs)


def logs(f_flag: bool = False, n_lines: int = 10):
    if not os.path.exists(LOG_FILE):
        print("No logs found")
        return

    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
        print("".join(lines[-n_lines:]), end="", flush=True)

    if f_flag:
        for line in watch_log_file():
            print(line, end="", flush=True)
    else:
        print()
