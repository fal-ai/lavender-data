from concurrent.futures import ProcessPoolExecutor

from lavender_data.server.background_worker.memory import Memory
from lavender_data.server.settings import get_settings, Settings
from lavender_data.server.db import setup_db
from lavender_data.server.cache import setup_cache
from lavender_data.server.reader import setup_reader
from lavender_data.server.registries import setup_registries


class BackgroundWorker:
    def __init__(self, num_workers: int):
        self._executor = ProcessPoolExecutor(
            num_workers,
            initializer=BackgroundWorker._initializer,
            initargs=(get_settings(),),
        )
        self._memory = Memory()

    @staticmethod
    def _initializer(settings: Settings):
        setup_db(settings.lavender_data_db_url)
        setup_cache(redis_url=settings.lavender_data_redis_url)
        setup_registries(settings.lavender_data_modules_dir)
        setup_reader(settings.lavender_data_reader_disk_cache_size)

    def submit(self, func, *args, **kwargs):
        return self._executor.submit(func, *args, **kwargs, memory=self._memory)

    def shutdown(self):
        self._executor.shutdown(wait=True)

    def memory(self) -> Memory:
        return self._memory
