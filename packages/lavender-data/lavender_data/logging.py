import os
import logging

formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(name)s: %(message)s")


def get_handlers():
    sh = logging.StreamHandler()
    # CRITICAL, ERROR, WARNING, INFO, DEBUG
    configured_log_level = os.environ.get("LAVENDER_DATA_LOG_LEVEL", "INFO")
    if configured_log_level == "CRITICAL":
        sh_log_level = logging.CRITICAL
    elif configured_log_level == "ERROR":
        sh_log_level = logging.ERROR
    elif configured_log_level == "WARNING":
        sh_log_level = logging.WARNING
    elif configured_log_level == "INFO":
        sh_log_level = logging.INFO
    elif configured_log_level == "DEBUG":
        sh_log_level = logging.DEBUG
    else:
        raise ValueError(f"Invalid log level: {configured_log_level}")
    sh.setLevel(sh_log_level)
    sh.setFormatter(formatter)

    filename = os.environ.get(
        "LAVENDER_DATA_LOG_FILE",
        os.path.expanduser("~/.lavender-data/server.log"),
    )
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    fh = logging.FileHandler(filename=filename)
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
