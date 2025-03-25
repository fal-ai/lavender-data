import logging


def get_logger(name: str):
    logger = logging.getLogger(name)
    if len(logger.handlers) > 0:
        # logger already initialized
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(name)s: %(message)s")

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)

    fh = logging.FileHandler(filename="lavender_data.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(sh)
        logger.addHandler(fh)

    return logger
