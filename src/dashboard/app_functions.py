import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import os
import sys
sys.path.append(os.path.abspath('./src/dashboard'))
sys.path.append(os.path.abspath('./src'))

from theme import PLOTLY_LAYOUT, PLOTLY_COLORSCALES, COLORS
import plotly.graph_objects as go

from db_functions import DotaDB

db = DotaDB(schema='public')

##### Theming
def apply_fig_theme(fig: go.Figure):
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig

##### Basic and filter helpers

def get_total_matches(clauses: str='', params=None):
    query = 'SELECT COUNT(*) FROM match_details md '
    if clauses:
        query += clauses
    return db.query_select(query, params=params)[0][0]

def get_leagues(dates):
    base_where = 'WHERE 1=1 AND ld."displayName" NOT LIKE \'?%%\' AND ld."displayName" NOT LIKE \'%%?\''
    if dates[0]:
        base_where, params = handle_date_filter(dates, base_where, [])
    else:
        params = None
    query = f'''
        SELECT DISTINCT ld."displayName" dn
        FROM match_details md
            INNER JOIN league_details ld ON md."leagueId" = ld.id 
        {base_where} 
        ORDER BY ld."displayName" ASC;
    ''' #TODO clean the base_where from here
    leagues = [result[0] for result in db.query_select(query, params=params)]
    return leagues

def get_date_boundary(boundary, league): 
    if league:
        query = f'''
            SELECT {boundary}(md."startDateTimeHuman") 
            FROM match_details md
            INNER JOIN league_details ld
            ON md."leagueId" = ld.id
            WHERE ld."displayName" = %s;
        '''
        return db.query_select(query, params=(league, ))[0][0]
    else:
        return db.query_select(f'SELECT {boundary}("startDateTimeHuman") FROM match_details;')[0][0]

def convert_duration_format(duration: int) -> str:
    duration = round(duration)
    minutes = str(duration // 60)
    seconds = str(duration % 60)
    if len(seconds) == 1: #TODO: collapse into one 
        seconds += '0'
    return minutes + ':' + seconds

def handle_date_filter(dates, where=None, params=None):
    if dates[0]:
        where += ' AND md."startDateTimeHuman" BETWEEN %s AND %s'
        start_date = dates[0]
        if dates[0] and dates[1]:
            end_date = datetime.fromisoformat(dates[1]) + timedelta(days=1)
        else:
            end_date = datetime.fromisoformat(dates[0]) + timedelta(days=1)
        params.extend([start_date, end_date])
        return where, params
    return where, params

##### Overview graph helpers
def get_match_ids(query, params):
    return [res[0] for res in db.query_select(query, params=params)]

def handle_filters(**kwargs):
    where = ' WHERE 1=1'
    join = ''
    params = []
    if kwargs['league']:
        where += ' AND ld."displayName" = %s'
        join += ' JOIN league_details ld ON md."leagueId" = ld.id'
        params.append(kwargs['league'])
    if kwargs['dates'][0]:
        where, params = handle_date_filter(dates=kwargs['dates'], where=where, params=params)
    clauses = join + where
    return clauses, params



