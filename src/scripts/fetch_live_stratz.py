import os
import sys
sys.path.append('./src')
import httpx
from dota_db import DotaDB
import logging
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
from basic_logger import setup_logger
listener = setup_logger(logfile_path=f'{str(PROJECT_ROOT)}/logs/daily-stratz-fetch.log')

def main():
    db = DotaDB()
    fetched_ids = [r[0] for r in db.select("SELECT match_id FROM live_matches WHERE status = 'fetched_opendota' OR status = 'failed_parse'")]
    with httpx.Client(headers=db.stratz_headers) as client:
        for mid in fetched_ids:    
            is_saved = db.try_fetch_stratz_match(client, mid)
            if is_saved:
                db.query_execute('DELETE FROM live_matches WHERE match_id = %s', params=(mid, ))
                db.query_execute('REFRESH MATERIALIZED VIEW hero_pick_ban_stats;')
                db.query_execute('REFRESH MATERIALIZED VIEW hero_winrate_stats')
                logging.info(f'Successfully saved data for archived live match ID {mid}')

if __name__ == '__main__':
    main()