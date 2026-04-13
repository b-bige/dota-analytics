import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))

from live_match_monitor import monitor
import logging
from basic_logger import setup_logger
listener = setup_logger(logfile_path=f'{str(PROJECT_PATH)}/logs/live-match-monitor.log')

#TEST
if __name__ == "__main__":
    monitor.run_forever(interval=180)