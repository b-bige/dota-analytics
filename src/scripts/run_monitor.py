import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from live_match_monitor import monitor
import logging
from basic_logger import setup_logger
listener = setup_logger(logfile_path='logs/live-match-monitor.log')

#TEST
if __name__ == "__main__":
    monitor.run_forever(interval=60)