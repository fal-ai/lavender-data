import os
import atexit
import signal
import select
import time
from multiprocessing import Process
import daemon
from daemon.pidfile import PIDLockFile

from .run import run

PID_LOCK_FILE = "/tmp/lavender-data.pid"
LOG_FILE = os.path.expanduser("~/.lavender-data/server.terminal.log")
WORKING_DIRECTORY = os.path.expanduser("~/.lavender-data/")

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

    process = Process(target=_run, args=args, kwargs=kwargs)
    process.start()
    atexit.register(lambda: process.terminate())

    ui_url = None
    for line in watch_log_file():
        if not process.is_alive():
            print(f"Failed to start server (check {LOG_FILE} for more details)")
            exit(1)

        if "lavender-data.server.ui" in line and "Network" in line:
            try:
                ui_url = line.split("http://")[1].split("\n")[0]
            except Exception:
                pass

        if "Uvicorn running on" in line:
            url = line.split("http://")[1].split("\n")[0].split(" ")[0]
            break

    print(f"lavender-data is running on {url}")
    if ui_url is not None:
        print(f"UI is running on {ui_url}")

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
        print("".join(lines[-n_lines:]))

    if f_flag:
        for line in watch_log_file():
            print(line, end="")
