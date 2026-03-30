import sys
import os

# Ensure the script can find your 'src' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the monitor instance from your file
# (Replace 'your_monitor_file' with the actual filename where your code lives)
from live_match_monitor import monitor

if __name__ == "__main__":
    monitor.run_forever(interval=60)