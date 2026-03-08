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

_winrate_fig, _picked_fig, _banned_fig  = get_top_heroes_graphs()

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
        Output('top-five-hero-winrate', 'figure'),
        Output('top-five-picked', 'figure'),
        Output('top-five-banned', 'figure'),
        State('url', 'pathname'),
        Input('league-filter', 'value'),
        Input('date-filter', 'value')
)
def update_top_heroes(pathname, league, dates):
    t = time.time()
    if pathname != '/':
        return no_update
    ### Handling filtering
    logging.info(f'update_top_heroes: {time.time()-t:.2f}s")')
    return get_top_heroes_graphs(league, dates)

@callback(
        Output('total-matches', 'children'),
        Output('stat-radiant-win', 'children'),
        Output('stat-avg-duration', 'children'),
        State('url', 'pathname'),
        Input("league-filter", "value"),
        Input("date-filter", "value")
)
def update_overview_stats(pathname, league, dates):
    t = time.time()
    if pathname != '/':
        return no_update
    clauses, params = handle_filters(league=league, dates=dates)
    rw_query = '''
        SELECT AVG(CAST("didRadiantWin" AS INT)) 
        FROM match_details md 
    ''' + clauses
    agl_query = '''
        SELECT AVG("durationSeconds") 
        FROM match_details md 
    ''' + clauses
    radiant_win = str(round(db.query_select(rw_query, params=params)[0][0], 2)) + '%'
    avg_game_length = convert_duration_format(db.query_select(agl_query, params=params)[0][0])
    found_matches = get_total_matches(clauses, params=params)
    logging.info(f'update_overview_stats: {time.time()-t:.2f}s")')
    return found_matches, radiant_win, avg_game_length

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


