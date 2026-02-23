import httpx
import pandas as pd
import numpy as np
import psycopg
from datetime import datetime, timedelta, timezone

import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

from dota_data_manager import DotaDataManager
from db_functions import DotaDB
from ratelimit import limits, sleep_and_retry

import logging
import basic_logger
basic_logger.setup_logger()

def main():
    db = DotaDB()
    dota_data = DotaDataManager(db)
    main_league_ids = dota_data.main_leagues
    #TODO: add a check so we only check the matches after the latest match date in database
    query = ''' 
        query($id: Int!, $request: LeagueMatchesRequestType!) {
            league(id: $id) {
                matches(request: $request) {
                    id
                    startDateTime
                }
            }
        }
    '''
    match_ids = []
    for league_id in main_league_ids:
        skip_counter = 0
        while True:
            results = db.query_stratz(
                query,  
                variables={
                    'id': int(league_id), 
                    'request': {'isParsed': True, 'take':100, 'skip': skip_counter}})
            results_matches = results['data']['league']['matches']
            skip_counter += 100
            if len(results_matches) == 0:
                break
            for res in results_matches:
                match_ids.append(res['id'])
    current_match_ids = [mid[0] for mid in db.query_select('SELECT id FROM match_details')]
    for mid in match_ids.copy():
        if mid in current_match_ids:
            match_ids.remove(mid)

    db.query_matches(match_ids)

if __name__ == '__main__':
    main()

