import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

import time
import logging

from theme import PLOTLY_COLORSCALES, COLORS

from app_functions import *

dash.register_page(__name__, path='')

_winrate_fig = get_top_winrate(QueryBuilder())
_picked_fig  = get_most_picked(QueryBuilder())
_banned_fig  = get_most_banned(QueryBuilder())

def layout(**kwargs):
    return [
        html.Div(
            style={
                "display": "flex",
                "width": "100%",
                "justifyContent": "space-evenly",
                'marginBottom': 20
            },
            children=[
                stat_card("Total Matches", id="total-matches"),
                stat_card("Win Rate (Radiant)", id="stat-radiant-win"),
                stat_card("Avg Game Length", id="stat-avg-duration"),
                # stat_card("Avg Kills", id="stat-total-kills"),
            ]
        ),
        html.Div(
            style={
                "display": "flex",
                "width": "100%",
                'alignItems': 'flex-start'
            },
            children=[
                dcc.Graph(
                    id='top-five-hero-winrate',
                    figure=_winrate_fig
                ),
            ]
        ),
        html.Div(
            style={
                "display": "flex",
                "width": "100%",
                'alignItems': 'flex-start'
            },
            children=[
                dcc.Graph(
                    id='top-five-picked',
                    figure=_picked_fig
                ),
            ]
        ),
        html.Div(
            style={
                "display": "flex",
                "width": "100%",
                'alignItems': 'flex-start'
            },
            children=[
                dcc.Graph(
                    id='top-five-banned',
                    figure=_banned_fig
                ),
            ]
        )
    ]

@callback(
        Output('total-matches', 'children'),
        Output('stat-radiant-win', 'children'),
        Output('stat-avg-duration', 'children'),
        Output('top-five-hero-winrate', 'figure'),
        Output('top-five-picked', 'figure'),
        Output('top-five-banned', 'figure'),
        State('url', 'pathname'),
        Input('patch-filter', 'value'),
        Input("league-filter", "value"),
        Input('teams-filter', 'value'),
        Input("date-filter", "value"),
        prevent_initial_call=True
)
def update_overview(pathname, patch, league, teams, dates):
    if pathname != '/':
        return no_update
    qb = QueryBuilder()
    qb = handle_filters(qb, patch=patch, league=league, teams=teams, dates=dates)
    query, params = qb.build(
        select='''
            COUNT(*),
        AVG(CAST("didRadiantWin" AS INT)),
        AVG("durationSeconds")
        '''
    )
    results = db.query_select(query, params=params)[0]
    found_matches = results[0]
    radiant_win = str(round(results[1], 2)) + '%'
    avg_game_length = convert_duration_format(results[2]) 
    winrate_fig = get_top_winrate(qb.copy())
    picked_fig = get_most_picked(qb.copy())
    banned_fig = get_most_banned(qb.copy())
    return found_matches, radiant_win, avg_game_length, winrate_fig, picked_fig, banned_fig

def stat_card(label, id):
    return dmc.Paper(
        withBorder=True,
        p='lg',
        w=200,
        children=[
            dmc.Text(label, size='xs', c='dimmed', fw=700, tt="uppercase"),
            dmc.Title("0", id=id, order=2)
        ]
    )


