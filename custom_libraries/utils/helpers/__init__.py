import logging
import sys

DEFAULT_FORMAT = "[%(levelname)s - %(name)s - %(message)s]"


def get_logger(name: str, stream=sys.stderr, log_fmt=None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(log_fmt or DEFAULT_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger