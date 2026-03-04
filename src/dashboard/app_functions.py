import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import os
import sys
sys.path.append(os.path.abspath('./src/dashboard'))
sys.path.append(os.path.abspath('./src'))

from db_functions import DotaDB

db = DotaDB(schema='public')

def get_total_matches(modifiers: str=''):
    query = 'SELECT COUNT(*) FROM match_details md '
    if modifiers:
        query += modifiers
    return db.query_select(query)[0][0]

def get_leagues():
    leagues = [result[0] for result in db.query_select(
        '''
            SELECT DISTINCT ld."displayName" dn
            FROM match_details md
                INNER JOIN league_details ld ON md."leagueId" = ld.id ORDER BY ld."displayName" ASC;
        '''
    )]
    return leagues

def get_date_boundary(boundary, league): 
    if league:
        query = f'''
            SELECT {boundary}(md."startDateTime") 
            FROM match_details md
            INNER JOIN league_details ld
            ON md."leagueId" = ld.id
            WHERE ld."displayName" = %s;
        '''
        return datetime.fromtimestamp(db.query_select(query, params=(league, ))[0][0])
    else:
        return datetime.fromtimestamp(db.query_select(f'SELECT {boundary}("startDateTime") FROM match_details;')[0][0])





