import os
import sys
import logging
from logging.handlers import WatchedFileHandler
import queue

def setup_logger(logfile_path):
    if not os.path.isabs(logfile_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logfile_path = os.path.join(base_dir, logfile_path)

    # Ensure log directory exists
    os.makedirs(os.path.dirname(logfile_path), exist_ok=True)

    log_queue = queue.Queue(-1)  # unlimited size

    # All handlers go on the queue listener, not the root logger
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    file_handler = logging.handlers.WatchedFileHandler(logfile_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '[PID: %(process)d] %(asctime)s - %(levelname)s - %(name)s - %(message)s'
    ))

    # Listener runs in its own thread, serialising all writes
    listener = logging.handlers.QueueListener(
        log_queue, console_handler, file_handler, respect_handler_level=True
    )
    listener.start()

    # Root logger just puts records on the queue
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(logging.handlers.QueueHandler(log_queue))

    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('dash').setLevel(logging.WARNING)

    return listener  # keep a reference so it isn't garbage collected