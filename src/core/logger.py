import os
import logging
import queue
import sys
from logging.handlers import WatchedFileHandler, QueueListener, QueueHandler

def setup_logger(logfile_path, level=logging.INFO):
    if not os.path.isabs(logfile_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logfile_path = os.path.join(base_dir, logfile_path)

    os.makedirs(os.path.dirname(logfile_path), exist_ok=True)

    log_queue = queue.Queue(-1)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    file_handler = WatchedFileHandler(logfile_path)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(
        '[PID: %(process)d] %(asctime)s - %(levelname)s - %(name)s - %(message)s'
    ))

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)

    listener = QueueListener(
        log_queue, console_handler, file_handler, stream_handler, respect_handler_level=True
    )
    listener.start()

    root_logger = logging.getLogger()
    if not any(isinstance(h, QueueHandler) for h in root_logger.handlers):
        root_logger.handlers.clear()
        root_logger.setLevel(level)
        root_logger.addHandler(QueueHandler(log_queue))

    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('dash').setLevel(logging.WARNING)

    return listener