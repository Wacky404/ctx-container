# TODO: Make sure the logs/ directory in cwd doesn't get program logs, put them in .ctxflow
"""
LOGGER SETUP FILE FOR CTX-CONTAINER
"""

from typing import Any
import logging
import logging.config
import logging.handlers
import atexit
import queue
from queue import Queue
import os

logger = logging.getLogger("CTX-CONTAINER")


def setup_logging(log_lvl_stdout: str | int = 'WARNING') -> None:
    log_queue: Queue[Any] = queue.Queue(-1)  # Infinite size
    os.makedirs("logs", exist_ok=True)  # Ensure log directory exists

    # Targets that QueueListener will push to
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(log_lvl_stdout)
    stdout_handler.setFormatter(
        logging.Formatter("%(levelname)s: %(message)s"))

    file_handler = logging.handlers.RotatingFileHandler(
        "logs/ctx-container.log", maxBytes=5_000_000, backupCount=5
    )
    file_handler.setLevel("DEBUG")
    file_handler.setFormatter(logging.Formatter(
        # "[%(levelname)s|%(module)s|L%(lineno)d|%(funcName)s] %(asctime)s: %(message)s",
        "[%(levelname)s|%(pathname)s|L%(lineno)d|%(funcName)s] %(asctime)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    ))

    # QueueHandler and QueueListener setup
    queue_handler = logging.handlers.QueueHandler(log_queue)
    listener = logging.handlers.QueueListener(
        log_queue, stdout_handler, file_handler, respect_handler_level=True
    )
    listener.start()
    atexit.register(listener.stop)

    # Set up logger
    root_logger = logging.getLogger()
    root_logger.setLevel("DEBUG")
    root_logger.handlers = []  # Clear any existing handlers
    root_logger.addHandler(queue_handler)

    # Optionally, configure your named logger as well
    work_logger = logging.getLogger("WorkLogger")
    work_logger.setLevel("DEBUG")
