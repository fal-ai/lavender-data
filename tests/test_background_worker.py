import unittest
import time
from lavender_data.server.background_worker import (
    setup_background_worker,
    get_background_worker,
)


def sleep_task(amount: int, memory, task_uid):
    time.sleep(amount)


def sleep_task_with_error(amount: int, memory, task_uid):
    time.sleep(amount)
    raise Exception("Error")


class TestBackgroundWorker(unittest.TestCase):
    def setUp(self):
        setup_background_worker(1)
        self.worker = get_background_worker()

    def test_submit(self):
        timeout = 5
        completed = False

        def on_complete(_):
            nonlocal completed
            completed = True

        self.worker.submit(sleep_task, amount=0.1, on_complete=on_complete)

        start_time = time.time()
        while not completed:
            time.sleep(0.1)
            if time.time() - start_time > timeout:
                raise Exception("Timeout")

    def test_running_tasks(self):
        timeout = 5
        completed = False

        def on_complete(_):
            nonlocal completed
            completed = True

        self.assertEqual(len(self.worker.running_tasks()), 0)
        self.worker.submit(sleep_task, amount=0.1, on_complete=on_complete)
        self.assertEqual(len(self.worker.running_tasks()), 1)
        self.assertEqual(self.worker.running_tasks()[0].name, "sleep_task")
        self.assertEqual(self.worker.running_tasks()[0].kwargs, {"amount": 0.1})

        start_time = time.time()
        while not completed:
            time.sleep(0.1)
            if time.time() - start_time > timeout:
                raise Exception("Timeout")

        self.assertEqual(len(self.worker.running_tasks()), 0)

    def test_submit_with_error(self):
        timeout = 5
        completed = False
        error = False

        def on_complete(_):
            nonlocal completed
            completed = True

        def on_error(_):
            nonlocal error
            error = True

        self.worker.submit(
            sleep_task_with_error,
            amount=0.1,
            on_complete=on_complete,
            on_error=on_error,
        )

        start_time = time.time()
        while not (completed or error):
            time.sleep(0.1)
            if time.time() - start_time > timeout:
                raise Exception("Timeout")

        self.assertFalse(completed)
        self.assertTrue(error)
