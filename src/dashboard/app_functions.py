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
import plotly.express as px

import logging
import time

from db_functions import DotaDB
from dashboard.query_builder import *
from dashboard.filters import *

db = DotaDB(schema='public')
_DB_MAX_DURATION = None

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

def get_max_duration(**kwargs):
    qb = QueryBuilder()
    qb = handle_filters(qb, **kwargs)
    query, params = qb.build(select='MAX("durationSeconds") / 60')
    return db.query_select(query, params=params)[0][0]

def get_url_data(params:dict, **kwargs):
    data = []
    for filter_name in kwargs.keys():
        match filter_name:
            case 'patch': #TODO omptimal way to check this?
                data.append(get_patches(**kwargs, exclude=filter_name if params.get(filter_name, None) else None))
            case 'league':
                data.append(get_leagues(**kwargs, exclude=filter_name if params.get(filter_name, None) else None))
            case 'teams':
                data.append(get_teams(**kwargs, exclude=filter_name if params.get(filter_name, None) else None))
    data.append(get_date_boundary('MIN', **kwargs, exclude='dates')) ##TODO Check if this is alright?
    data.append(get_date_boundary('MAX', **kwargs, exclude='dates'))
    return tuple(data)

def get_filter_data(filter:str, **kwargs):
    match filter:
        case 'patch':
            return get_patches(**kwargs)
        case 'league':
            return get_leagues(**kwargs)
        case 'teams':
            return get_teams(**kwargs)

def get_teams(**kwargs):
    qb = QueryBuilder()
    qb.join('tdr', 'INNER JOIN team_details tdr ON tdr.id = md."radiantTeamId"')
    qb.join('tdd', 'INNER JOIN team_details tdd ON tdd.id = md."direTeamId"')
    qb.where('tdr."isPro" = \'t\' AND tdd."isPro" = \'t\'')
    handle_filters(qb, **kwargs)
    q1, params1 = qb.build(select='DISTINCT tdr.name')
    q2, params2 = qb.copy().build(select='DISTINCT tdd.name')

    query = f'''
        {q1}
        UNION
        {q2}
        ORDER BY name ASC
    '''
    return [r[0] for r in db.query_select(query, params=params1 + params2)]

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

def handle_filters(qb: QueryBuilder, exclude=None, **kwargs):
    if kwargs.get('league') and kwargs.get('exclude', None) != 'league':
        qb.join('ld', 'LEFT JOIN league_details ld ON md."leagueId" = ld.id')
        qb.where('ld."displayName" = %s', kwargs['league'])

    if kwargs.get('patch') and kwargs.get('exclude', None) != 'patch':
        qb.join('p', 'LEFT JOIN patches p ON md."gameVersionId" = p.id')
        qb.where('p.name = %s', kwargs['patch'])

    if kwargs.get('teams') and kwargs.get('exclude', None) != 'teams':
        teams = kwargs.get('teams')
        if teams[0]:
            qb.join('radiant', 'LEFT JOIN team_details radiant ON radiant.id = md."radiantTeamId"')
            qb.join('dire', 'LEFT JOIN team_details dire ON dire.id = md."direTeamId"')
            if len(teams) == 2:
                qb.where(
                    '(radiant.name = %s AND dire.name = %s) OR (radiant.name = %s AND dire.name = %s)',
                    teams[0], teams[1], teams[1], teams[0]
                )
            else:
                qb.where('(radiant.name = ANY(%s)) OR (dire.name = ANY(%s))', teams, teams)

    if kwargs.get('durations') and kwargs.get('exclude', None) != 'durations':
        start, end = kwargs.get('durations')
        start = int(start)*60 if start else 0
        end = int(end)*60 if end else get_db_max_duration()
        if start and start != 0:
            qb.where('md."durationSeconds" > %s', start)
        if end and end != get_db_max_duration()*60:
            qb.where('md."durationSeconds" < %s', end)

    if kwargs.get('dates', [None])[0] and kwargs.get('exclude', None) != 'dates':
        start, end = handle_date_filter(kwargs['dates'])
        qb.where('md."startDateTimeHuman" BETWEEN %s AND %s', start, end)
    return qb

def handle_date_filter(dates):
    if dates[0]:
        start_date = datetime.fromisoformat(dates[0])
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

def fig_most_picked(qb: QueryBuilder, match_count):
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
    most_picked['picks'] = (most_picked['picks'] / match_count).round(2) 
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=most_picked['picks'],
        y=most_picked['hero'],
        orientation='h',
        marker=dict(
            color=most_picked['picks'],
            colorscale=PLOTLY_COLORSCALES['colorscale'],
            showscale=False,
        ),
        text=[f"{picks:.0%}" for picks in most_picked['picks']],
        textposition='outside'
    ))
    fig = apply_fig_theme(fig)
    fig.update_layout(
        title="Top 5 picked heroes",
        autosize=True,
        xaxis=dict(title_text='Pick rate', tickformat=".0%", range=[0, max(most_picked['picks']) * 1.15], showgrid=False),
        yaxis=dict(showgrid=False)
    )
    return fig

def fig_most_banned(qb:QueryBuilder, match_count):
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
    most_banned['bans'] = (most_banned['bans'] / match_count).round(2) 
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=most_banned['bans'],
        y=most_banned['hero'],
        orientation='h',
        marker=dict(
            color=most_banned['bans'],
            colorscale=PLOTLY_COLORSCALES['colorscale'],
            showscale=False,
        ),
        text=[f"{bans:.0%}" for bans in most_banned['bans']],
        textposition='outside'
    ))
    fig = apply_fig_theme(fig)
    fig.update_layout(
        title="Top 5 banned heroes",
        autosize=True,
        xaxis=dict(title_text='Ban rate', tickformat=".0%", range=[0, max(most_banned['bans']) * 1.15], showgrid=False),
        yaxis=dict(showgrid=False)
    )
    return fig

def fig_top_winrate(qb: QueryBuilder, match_count):
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
            colorscale=PLOTLY_COLORSCALES['colorscale'],
            showscale=False,
        ),
        customdata=winrates['picks'],
        text=[f"{w:.0%}" for w in winrates['winrate']],
        textposition='outside'
    ))
    fig = apply_fig_theme(fig)
    fig.update_layout(
        title="Top 5 heroes by winrate",
        autosize=True,
        xaxis=dict(title_text='Winrate', tickformat=".0%",
                   range=[0, max(winrates['winrate']) * 1.15], showgrid=False),
        yaxis=dict(showgrid=False)
    )
    return fig

def fig_most_present(qb: QueryBuilder, match_count):
    if not qb.is_filtered():
        results = db.query_select(
            '''SELECT presence, "displayName" 
               FROM hero_presence_stats
               ORDER BY presence DESC LIMIT 5'''
        )
    else:
        qb.join('mpb', 'JOIN match_pick_bans mpb ON md.id = mpb.match_id')
        qb.join('hd_mpb', 'JOIN hero_details hd ON hd.id = mpb."heroId"')
        query, params = qb.build(
            select='COUNT(*) AS presence, hd."displayName"',
            order_by='GROUP BY hd."displayName" ORDER BY presence DESC LIMIT 5'
        )
        results = db.query_select(query, params=params)
    most_present = pd.DataFrame(results, columns=['presence', 'hero']).sort_values('presence')
    most_present['presence'] = (most_present['presence'] / match_count).round(2)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=most_present['presence'],
        y=most_present['hero'],
        orientation='h',
        marker=dict(
            color=most_present['presence'],
            colorscale=PLOTLY_COLORSCALES['colorscale'],
            showscale=False,
        ),
        text=[f"{pres:.0%}" for pres in most_present['presence']],
        textposition='outside'
    ))
    fig = apply_fig_theme(fig)
    fig.update_layout(
        title="Top 5 present heroes",
        autosize=True,
        xaxis=dict(title_text='Presence rate', tickformat=".0%", range=[0, max(most_present['presence']) * 1.15], showgrid=False),
        yaxis=dict(showgrid=False)
    )
    return fig

def fig_duration_hist(qb: QueryBuilder):
    query, params = qb.build(select='"durationSeconds" / 60')
    results = pd.Series([r[0] for r in db.query_select(query, params=params)])
    fig = px.histogram(results, nbins=30, color_discrete_sequence=[COLORS['primary']])
    fig = apply_fig_theme(fig)
    fig.update_traces(
        patch={
            'marker': dict(
                showscale=False,
                line=dict(
                    color=COLORS['bg_elevated'], # gap between bars
                    width=1
                )
            )
        }
    )
    fig.update_layout(
        title="Match duration",
        autosize=True,
        xaxis=dict(showgrid=False, title_text='Match Duration Distribution', ticksuffix='m'),
        yaxis=dict(showgrid=False, title_text='Number of Matches'),
        showlegend=False
    )
    return fig

#### Update helpers
def update_url_from_filters_helper(params, filters):
    for filter_name, value in filters.items():
        params.update(FILTER_MAP[filter_name].to_url_params(value))
    return params

def get_db_max_duration(): #TODO: Update this so it updates, or maybe move this to a materialized view and trigger updates
    query = 'SELECT MAX("durationSeconds") / 60 FROM match_details'
    return db.query_select(query)[0][0]