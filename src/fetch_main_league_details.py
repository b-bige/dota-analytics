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

import db_functions as dbf
from ratelimit import limits, sleep_and_retry

import logging
import basic_logger
basic_logger.setup_logger()

def main():
    db = dbf.DotaDB()
    queries = [
        'SELECT id FROM league_details ld WHERE ld."displayName" LIKE \'ESL%\' AND ld."prizePool" <> 0;',
        'SELECT id FROM league_details ld WHERE ld."displayName" LIKE \'%DreamLeague%\' AND ld."prizePool" <> 0;',
        'SELECT id FROM league_details ld WHERE ld."displayName" LIKE \'%International%\' AND ld."prizePool" <> 0;',
        'SELECT id FROM league_details ld WHERE ld."displayName" LIKE \'FISSURE%\' AND ld."displayName" NOT LIKE \'%Special\' AND ld."prizePool" <> 0;',
        'SELECT id FROM league_details ld WHERE ld."displayName" LIKE \'%Clavision%\' AND ld."prizePool" <> 0;'
    ]
    league_ids = []
    for query in queries:
        for lid in [res[0] for res in db.query_select(query)]:
            league_ids.append(lid)
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
    for league_id in league_ids:
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

