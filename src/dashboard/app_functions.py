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

def get_total_matches(modifiers: str='', params=None):
    query = 'SELECT COUNT(*) FROM match_details md '
    if modifiers:
        query += modifiers
    return db.query_select(query, params=params)[0][0]

def get_leagues(dates):
    base_where = 'WHERE 1=1'
    if dates[0]:
        base_where, params = handle_date_filter(dates, base_where, [])
    else:
        params = None
    
    leagues = [result[0] for result in db.query_select(
        f'''
            SELECT DISTINCT ld."displayName" dn
            FROM match_details md
                INNER JOIN league_details ld ON md."leagueId" = ld.id 
            {base_where}
            ORDER BY ld."displayName" ASC;
        ''', params=params 
    )]
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

def handle_date_filter(dates, base_where=None, params=None):
    if dates[0]:
        base_where += ' AND md."startDateTimeHuman" BETWEEN %s AND %s'
        start_date = dates[0]
        if dates[0] and dates[1]:
            end_date = datetime.fromisoformat(dates[1]) + timedelta(days=1)
        else:
            end_date = datetime.fromisoformat(dates[0]) + timedelta(days=1)
        params.extend([start_date, end_date])
        return base_where, params
    return base_where, params

##### Overview graph helpers
def get_match_ids(query, params):
    return [res[0] for res in db.query_select(query, params=params)]




