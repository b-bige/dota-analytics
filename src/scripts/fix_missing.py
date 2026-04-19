import sys
import os
sys.path.append(os.path.abspath('./src'))
from dota_db import DotaDB
from live_match_monitor import LiveMatchMonitor
import httpx
import logging
from basic_logger import setup_logger
db = DotaDB()

setup_logger(logfile_path='logs/fix_missing.log')

def main():
    query = '''
        SELECT id 
        FROM match_details 
        WHERE id NOT IN 
        (SELECT DISTINCT match_id FROM match_players)
    '''
    match_ids = [r[0] for r in db.select(query)]
    print(len(match_ids))
    db.fetch_stratz_matches(match_ids)

if __name__ == '__main__':
    main()
