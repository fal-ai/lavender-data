import os
import logging

formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(name)s: %(message)s")


def get_handlers(log_level: int, is_worker: bool):

    sh = logging.StreamHandler()
    sh.setLevel(log_level)
    sh.setFormatter(formatter)

    filename = os.environ.get(
        "LAVENDER_DATA_LOG_FILE",
        os.path.expanduser("~/.lavender-data/server.log"),
    )
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    fh = logging.FileHandler(filename=filename)
    fh.setLevel(logging.DEBUG)  # always log to file
    fh.setFormatter(formatter)

    handlers = []
    if not is_worker:
        handlers.append(sh)
    handlers.append(fh)

    return handlers


def _log_level_to_int(log_level: str) -> int:
    if log_level == "CRITICAL":
        return logging.CRITICAL
    elif log_level == "ERROR":
        return logging.ERROR
    elif log_level == "WARNING":
        return logging.WARNING
    elif log_level == "INFO":
        return logging.INFO
    elif log_level == "DEBUG":
        return logging.DEBUG
    else:
        raise ValueError(f"Invalid log level: {log_level}")


def get_logger(
    name: str,
    *,
    clear_handlers: bool = False,
):
    is_worker = os.environ.get("LAVENDER_DATA_IS_WORKER", "false").lower() == "true"
    logger = logging.getLogger(
        name if not is_worker else f"[worker_pid={os.getpid()}]{name}"
    )

    if clear_handlers:
        logger.handlers.clear()

    if len(logger.handlers) == 0:
        # CRITICAL, ERROR, WARNING, INFO, DEBUG
        logger.setLevel(logging.DEBUG)
        log_level = _log_level_to_int(os.environ.get("LAVENDER_DATA_LOG_LEVEL", "INFO"))

        for handler in get_handlers(
            log_level=log_level,
            is_worker=is_worker,
        ):
            logger.addHandler(handler)

    return logger
