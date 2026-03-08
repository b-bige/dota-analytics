import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import httpx

import concurrent.futures

import os
import sys
sys.path.append(os.path.abspath('./src/dashboard'))
sys.path.append(os.path.abspath('./src'))

from theme import PLOTLY_LAYOUT, PLOTLY_COLORSCALES, COLORS
import plotly.graph_objects as go

import logging
import time

from db_functions import DotaDB

db = DotaDB(schema='public')

##### Theming
def apply_fig_theme(fig: go.Figure):
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig

##### Basic and filter helpers

def get_total_matches(clauses: str='', params=None):
    query = 'SELECT COUNT(id) FROM match_details md '
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
        join += ' LEFT JOIN league_details ld ON md."leagueId" = ld.id'
        params.append(kwargs['league'])
    if kwargs['dates'][0]:
        where, params = handle_date_filter(dates=kwargs['dates'], where=where, params=params)
    clauses = join + where
    return clauses, params

def get_most_picked(clauses, params):
    if clauses == ' WHERE 1=1' and len(params) == 0:
        results = db.query_select(
            '''
                SELECT picks, "displayName" 
                FROM hero_pick_ban_stats 
                ORDER BY picks DESC 
                LIMIT 5
            '''
        )
    else:
        query = f'''
            SELECT
                COUNT(*) FILTER (WHERE mpb."isPick" = TRUE) AS count,
                hd."displayName"
            FROM match_pick_bans mpb
            JOIN hero_details hd
            ON hd.id = mpb."heroId"
            JOIN match_details md
            ON md.id = mpb.match_id
            {clauses}
            GROUP BY hd."displayName", hd."shortName"
            ORDER BY count DESC
            LIMIT 5;
        '''
        
        results = db.query_select(query, params=params)
  # (count, display_name, npc_name)
    most_picked = pd.DataFrame(results, columns=['picks', 'hero']).sort_values(by='picks')
    picked_fig = go.Figure()
    picked_fig.add_trace(
        go.Bar(
            x=most_picked['picks'],
            y=most_picked['hero'],
            orientation='h',
            marker=dict(
                color=most_picked['picks'],        # use actual values for color mapping
                colorscale=PLOTLY_COLORSCALES['winrate'],
                showscale=False,                  # set True if you want the colorbar
            ),
        )
    )
    picked_fig = apply_fig_theme(picked_fig)
    picked_fig.update_layout(
        title="Top 5 picked heroes",
        width=600,
        xaxis=dict(title_text = 'Picks', range=[0, max(most_picked['picks']) * 1.15], showgrid=False),  # 15% breathing room
        yaxis=dict(showgrid=False)
    )
    
    return picked_fig

def get_most_banned(clauses, params):
    if clauses == ' WHERE 1=1' and len(params) == 0:
        results = db.query_select(
            '''
                SELECT bans, "displayName" 
                FROM hero_pick_ban_stats 
                ORDER BY bans DESC 
                LIMIT 5
            '''
        )
    else:
        query = f'''
            SELECT
                COUNT(*) FILTER (WHERE mpb."isPick" = FALSE) AS count,
                hd."displayName"
            FROM match_pick_bans mpb
            JOIN hero_details hd
            ON hd.id = mpb."heroId"
            JOIN match_details md
            ON md.id = mpb.match_id
            {clauses}
            GROUP BY hd."displayName", hd."shortName"
            ORDER BY count DESC
            LIMIT 5;
        '''
        results = db.query_select(query, params=params)
    most_banned = pd.DataFrame(results, columns=['bans', 'hero']).sort_values(by='bans')
    banned_fig = go.Figure()
    banned_fig.add_trace(
        go.Bar(
            x=most_banned['bans'],
            y=most_banned['hero'],
            orientation='h',
            marker=dict(
                color=most_banned['bans'],        # use actual values for color mapping
                colorscale=PLOTLY_COLORSCALES['winrate'],
                showscale=False,                  # set True if you want the colorbar
            ),
        )
    )
    banned_fig = apply_fig_theme(banned_fig)
    banned_fig.update_layout(
        title="Top 5 banned heroes",
        width=600,
        xaxis=dict(title_text = 'Bans', range=[0, max(most_banned['bans']) * 1.15], showgrid=False),  # 15% breathing room
        yaxis=dict(showgrid=False)
    )
    
    return banned_fig

def get_top_winrate(clauses, params):
    query = 'SELECT COUNT(id) FROM match_details md' + clauses
    match_count = db.query_select(query, params=params)[0][0]
    min_picks = max(2, match_count // 10)
    if clauses == ' WHERE 1=1' and len(params) == 0:
        query = '''
            SELECT winrate, picks, "displayName"
            FROM hero_winrate_stats
            WHERE picks >= %s
            ORDER BY winrate DESC
            LIMIT 5;
        '''
        winrates = pd.DataFrame(
            db.query_select(query, params=(min_picks, )), #TODO reduce/clean unncessary/double lines  
            columns=['winrate', 'picks', 'hero']
        ).convert_dtypes().sort_values('winrate')
    else:
        query = f'''
            SELECT AVG(CAST(mp."isVictory" AS INT)) AS winrate,
                COUNT(*) as picks,
                hd."displayName"
            FROM match_players mp
            JOIN hero_details hd 
            ON mp."heroId" = hd.id
            JOIN match_details md
            ON mp.match_id = md.id
            GROUP BY hd."displayName"
            HAVING COUNT(*) >= %s
            ORDER BY winrate DESC
            LIMIT 5
        '''
        winrate_params = (*params, min_picks) if params else (min_picks, )
        winrates = pd.DataFrame(
            db.query_select(query, params=winrate_params), 
            columns=['winrate', 'picks', 'hero']
        ).convert_dtypes().sort_values('winrate')
    winrates['winrate'] = winrates['winrate'].astype('Float32')
    winrates['winrate'] = winrates['winrate'].round(2)
    winrate_fig = go.Figure()
    winrate_fig.add_trace(
        go.Bar(
            x=winrates['winrate'],
            y=winrates['hero'],
            orientation='h',
            marker=dict(
                color=winrates['winrate'],        # use actual values for color mapping
                colorscale=PLOTLY_COLORSCALES['winrate'],
                showscale=False,                  # set True if you want the colorbar
            ),
            customdata=winrates['picks'],
            text=[f"{w:.0%}" for w in winrates['winrate']],
            textposition='outside'
        )
    )
    winrate_fig = apply_fig_theme(winrate_fig)
    winrate_fig.update_layout(
        title="Top 5 heroes by winrate",
        width=600,
        xaxis=dict(title_text = 'Hero winrate', tickformat=".0%", range=[0, max(winrates['winrate']) * 1.15], showgrid=False),  # 15% breathing room
        yaxis=dict(showgrid=False)
    )
    return winrate_fig