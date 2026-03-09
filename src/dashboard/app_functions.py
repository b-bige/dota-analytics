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
from query_builder import QueryBuilder

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

def get_url_data(**kwargs):
    patch_data = get_patches(**kwargs)
    league_data = get_leagues(**kwargs)
    min_date = get_date_boundary('MIN', **kwargs)
    max_date = get_date_boundary('MAX', **kwargs)
    return patch_data, league_data, min_date, max_date

def get_patches(**kwargs):
    qb = QueryBuilder()
    qb.join('p', 'INNER JOIN patches p ON md."gameVersionId" = p.id')
    handle_filters(qb, **kwargs)  # will skip 'p' if already joined, add 'ld' if needed
    query, params = qb.build(
        select='DISTINCT p.name',
        order_by='ORDER BY p.name DESC'
    )
    return [result[0] for result in db.query_select(query, params=params)]

def get_leagues(**kwargs):
    qb = QueryBuilder()
    qb.join('ld', 'INNER JOIN league_details ld ON md."leagueId" = ld.id')
    handle_filters(qb, **kwargs)  # will skip 'ld' since already joined
    query, params = qb.build(
        select='DISTINCT ld."displayName"',
        extra_conditions='ld."displayName" NOT LIKE \'?%%\'',
        order_by='ORDER BY ld."displayName" ASC'
    )
    leagues = [result[0] for result in db.query_select(query, params=params)]
    return leagues

def get_date_boundary(boundary, **kwargs): 
    qb = QueryBuilder()
    handle_filters(qb, **kwargs)
    query, params = qb.build(
        select=f'{boundary}(md."startDateTimeHuman")'
    )
    return db.query_select(query, params=params)[0][0]

def handle_filters(qb: QueryBuilder, **kwargs):
    if kwargs.get('league') and kwargs.get('exclude', None) != 'league':
        qb.join('ld', 'LEFT JOIN league_details ld ON md."leagueId" = ld.id')
        qb.where('ld."displayName" = %s', kwargs['league'])

    if kwargs.get('patch') and kwargs.get('exclude', None) != 'patch':
        qb.join('p', 'LEFT JOIN patches p ON md."gameVersionId" = p.id')
        qb.where('p.name = %s', kwargs['patch'])

    if kwargs.get('dates', [None])[0] and kwargs.get('exclude', None) != 'dates':
        start, end = handle_date_filter(kwargs['dates'])
        qb.where('md."startDateTimeHuman" BETWEEN %s AND %s', start, end)

    return qb

def handle_date_filter(dates):
    if dates[0]:
        start_date = dates[0]
        if dates[0] and dates[1]:
            end_date = datetime.fromisoformat(dates[1]) + timedelta(days=1)
        else:
            end_date = datetime.fromisoformat(dates[0]) + timedelta(days=1)
    return [start_date, end_date]

def convert_duration_format(duration: int) -> str:
    duration = round(duration)
    minutes = str(duration // 60)
    seconds = str(duration % 60)
    if len(seconds) == 1: #TODO: collapse into one 
        seconds += '0'
    return minutes + ':' + seconds

##### Overview graph helpers
def get_match_ids(query, params):
    return [res[0] for res in db.query_select(query, params=params)]

def get_most_picked(qb):
    if not qb.is_filtered():
        results = db.query_select(
            '''SELECT picks, "displayName" 
               FROM hero_pick_ban_stats 
               ORDER BY picks DESC LIMIT 5'''
        )
    else:
        qb.join('mpb', 'JOIN match_pick_bans mpb ON md.id = mpb.match_id')
        qb.join('hd_mpb', 'JOIN hero_details hd ON hd.id = mpb."heroId"')
        query, params = qb.build(
            select='COUNT(*) FILTER (WHERE mpb."isPick" = TRUE) AS count, hd."displayName"',
            extra_conditions='',
            order_by='GROUP BY hd."displayName" ORDER BY count DESC LIMIT 5'
        )
        results = db.query_select(query, params=params)

    most_picked = pd.DataFrame(results, columns=['picks', 'hero']).sort_values('picks')
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=most_picked['picks'],
        y=most_picked['hero'],
        orientation='h',
        marker=dict(
            color=most_picked['picks'],
            colorscale=PLOTLY_COLORSCALES['winrate'],
            showscale=False,
        ),
    ))
    fig = apply_fig_theme(fig)
    fig.update_layout(
        title="Top 5 picked heroes",
        width=600,
        xaxis=dict(title_text='Picks', range=[0, max(most_picked['picks']) * 1.15], showgrid=False),
        yaxis=dict(showgrid=False)
    )
    return fig


def get_most_banned(qb):
    if not qb.is_filtered():
        results = db.query_select(
            '''SELECT bans, "displayName" 
               FROM hero_pick_ban_stats 
               ORDER BY bans DESC LIMIT 5'''
        )
    else:
        qb.join('mpb', 'JOIN match_pick_bans mpb ON md.id = mpb.match_id')
        qb.join('hd_mpb', 'JOIN hero_details hd ON hd.id = mpb."heroId"')
        query, params = qb.build(
            select='COUNT(*) FILTER (WHERE mpb."isPick" = FALSE) AS count, hd."displayName"',
            order_by='GROUP BY hd."displayName" ORDER BY count DESC LIMIT 5'
        )
        results = db.query_select(query, params=params)

    most_banned = pd.DataFrame(results, columns=['bans', 'hero']).sort_values('bans')
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=most_banned['bans'],
        y=most_banned['hero'],
        orientation='h',
        marker=dict(
            color=most_banned['bans'],
            colorscale=PLOTLY_COLORSCALES['winrate'],
            showscale=False,
        ),
    ))
    fig = apply_fig_theme(fig)
    fig.update_layout(
        title="Top 5 banned heroes",
        width=600,
        xaxis=dict(title_text='Bans', range=[0, max(most_banned['bans']) * 1.15], showgrid=False),
        yaxis=dict(showgrid=False)
    )
    return fig


def get_top_winrate(qb):
    count_query, params = qb.build(select='COUNT(md.id)')
    match_count = db.query_select(count_query, params=params)[0][0]
    min_picks = max(2, match_count // 10)

    if not qb.is_filtered():
        results = db.query_select(
            '''SELECT winrate, picks, "displayName"
               FROM hero_winrate_stats
               WHERE picks >= %s
               ORDER BY winrate DESC LIMIT 5''',
            params=(min_picks,)
        )
    else:
        qb.join('mp', 'JOIN match_players mp ON mp.match_id = md.id')
        qb.join('hd', 'JOIN hero_details hd ON mp."heroId" = hd.id')
        qb.having('COUNT(*) >= %s', min_picks)
        query, params = qb.build(
            select='AVG(CAST(mp."isVictory" AS INT)) AS winrate, COUNT(*) as picks, hd."displayName"',
            group_by='GROUP BY hd."displayName"',
            order_by='ORDER BY winrate DESC LIMIT 5'
        )
        results = db.query_select(query, params=params)

    winrates = (pd.DataFrame(results, columns=['winrate', 'picks', 'hero'])
                .convert_dtypes()
                .sort_values('winrate'))
    winrates['winrate'] = winrates['winrate'].astype('Float32').round(2)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=winrates['winrate'],
        y=winrates['hero'],
        orientation='h',
        marker=dict(
            color=winrates['winrate'],
            colorscale=PLOTLY_COLORSCALES['winrate'],
            showscale=False,
        ),
        customdata=winrates['picks'],
        text=[f"{w:.0%}" for w in winrates['winrate']],
        textposition='outside'
    ))
    fig = apply_fig_theme(fig)
    fig.update_layout(
        title="Top 5 heroes by winrate",
        width=600,
        xaxis=dict(title_text='Hero winrate', tickformat=".0%",
                   range=[0, max(winrates['winrate']) * 1.15], showgrid=False),
        yaxis=dict(showgrid=False)
    )
    return fig