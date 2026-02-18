import os
import logging
import sys

def initiate_basic_logger():
    log_dir = os.path.join(os.getcwd(), 'logs')
    print(log_dir)
    os.makedirs(log_dir, exist_ok=True)
    log_filepath = os.path.join(log_dir, 'hero_stats_weekly.log')

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_filepath)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout) # sys.stdout ensures it goes to the terminal
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s')) # Cleaner format for console
    logger.addHandler(console_handler)
    
    return logger