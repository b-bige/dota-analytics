import os
import sys
import pandas as pd
import numpy as np
sys.path.append(os.path.abspath('./src'))
import logging
from core.logger import setup_logger
from database.dota_db import DotaDB
listener = setup_logger(logfile_path='logs/update_dataset.log')

def main():
    db = DotaDB()
    february = pd.read_csv('data/main_metadata.csv')
    march = pd.read_csv('data/main_metadata (1).csv')
    april = pd.read_csv('data/main_metadata (2).csv')
    matches = pd.concat([february, march, april], axis=0)
    db_ids = [r[0] for r in db.select('SELECT id FROM match_details')]
    missing = []
    for mid in matches['match_id']:
        if mid not in db_ids:
            missing.append(mid)
    db.fetch_stratz_matches(missing)

if __name__ == '__main__':
    main()
