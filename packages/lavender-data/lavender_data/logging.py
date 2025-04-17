import os
import logging

formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(name)s: %(message)s")


def get_handlers():
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)

    fh = logging.FileHandler(
        filename=os.environ.get("LAVENDER_DATA_LOG_FILE", "lavender_data.log")
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    return [sh, fh]


def get_logger(name: str, *, clear_handlers: bool = False, level: int = logging.DEBUG):
    logger = logging.getLogger(name)

    if clear_handlers:
        logger.handlers.clear()

    if len(logger.handlers) == 0:
        logger.setLevel(level)
        for handler in get_handlers():
            logger.addHandler(handler)

    return logger
