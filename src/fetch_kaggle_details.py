import httpx
import pandas as pd
import numpy as np

import os
import sys
sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

from dota_data_manager import DotaDataManager
from db_functions import DotaDB

import logging
import basic_logger
basic_logger.setup_logger(logfile_path='logs/fetch_main_league_details.log')

def main():
    db = DotaDB(schema='kaggle')
    query = """
        SELECT match_id 
        FROM main_metadata 
        WHERE start_date_time < '2021-12-15 14:45:00'
        ORDER BY start_date_time DESC;
    """
    match_ids = [mid[0] for mid in db.query_select(query)]
    db.set_schema(schema='public')
    query = '''
        SELECT id 
        FROM match_details
    '''
    for current_id in [mid[0] for mid in db.query_select(query)]:
        if current_id in match_ids:
            match_ids.remove(current_id)
    logging.info(f'Starting collecting historical match data for {len(match_ids)} matches')
    db.query_matches(match_ids)

if __name__ == '__main__':
    main()