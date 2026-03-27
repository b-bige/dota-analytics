import os
import sys
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(logfile_path):
    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # 1. CRITICAL: Clear existing handlers so hot-reloads don't stack them
    

    # 1. Setup the Root Logger to catch everything (DEBUG or INFO)
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear() 
    root_logger.setLevel(logging.INFO)
    
    # 2. Console Handler: Shows everything INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO) 
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    # 3. File Handler: ONLY catches ERROR and CRITICAL
    file_handler = RotatingFileHandler(
        logfile_path, 
        maxBytes=5*1024*1024, 
        backupCount=10
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('[PID: %(process)d] %(asctime)s - %(levelname)s - %(message)s'))

    # 4. Add both to the root
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)