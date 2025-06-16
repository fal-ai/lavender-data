import os
import random
import time
import unittest

from lavender_data.server.cache import setup_cache
from lavender_data.server.background_worker import (
    TaskStatus,
    setup_background_worker,
    get_background_worker,
)


def write_task(filename: str):
    yield TaskStatus(status="write", current=0, total=1)
    time.sleep(0.1)
    with open(filename, "w") as f:
        f.write("Hello, world!")
    yield TaskStatus(status="write", current=1, total=1)


class TestBackgroundWorker(unittest.TestCase):
    def setUp(self):
        setup_cache()
        setup_background_worker(1)
        self.worker = get_background_worker()

    def tearDown(self):
        self.worker.shutdown()

    def test_submit(self):
        timeout = 5

        filename = f"test-{random.randint(0, 1000000)}.txt"
        self.worker.submit(write_task, filename=filename, with_status=True)

        start_time = time.time()
        while not os.path.exists(filename):
            time.sleep(0.1)
            if time.time() - start_time > timeout:
                raise Exception("Timeout")

        os.remove(filename)

    def test_running_tasks(self):
        timeout = 5

        filename = f"test-{random.randint(0, 1000000)}.txt"
        self.assertEqual(len(self.worker.running_tasks()), 0)
        self.worker.submit(write_task, filename=filename, with_status=True)
        self.assertEqual(len(self.worker.running_tasks()), 1)
        self.assertEqual(self.worker.running_tasks()[0].name, "write_task")
        self.assertEqual(self.worker.running_tasks()[0].kwargs, {"filename": filename})

        start_time = time.time()
        while not os.path.exists(filename):
            time.sleep(0.1)
            if time.time() - start_time > timeout:
                raise Exception("Timeout")

        os.remove(filename)
