import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

import time
import logging

from theme import PLOTLY_COLORSCALES, COLORS

from app_functions import *
from dashboard.filters import *

dash.register_page(__name__, path='')

_total_matches = get_total_matches()
_winrate_fig = fig_top_winrate(QueryBuilder(), _total_matches)
_duration_fig = fig_duration_hist(QueryBuilder())

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
            id='error-card',
            style={
                "display": "flex",
                "width": "100%",
                'alignItems': 'flex-start',
                'height': '0px',
            },
            children=[]
        ),
        html.Div(
            style={
                "display": "flex",
                "width": "100%",
                'alignItems': 'flex-start'
            },
            children=[
                html.Div(
                    style={
                        "display": "flex",
                        "width": "50%",
                        'alignItems': 'flex-start' 
                    },
                    children=[
                        dmc.Select(
                            id='top-heroes-select',
                            label='Top heroes by',
                            data=[
                                {'value': 'win', 'label': 'Win-rate'},
                                {'value': 'pick', 'label': 'Pick-rate'},
                                {'value': 'ban', 'label': 'Ban-rate'},
                                {'value': 'pres', 'label': 'Presence-rate (Pick & Ban)'}
                            ],
                            value='win',
                            w=300,
                            mb='md'
                        ),
                    ]
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
                    id='top-heroes',
                    figure=_winrate_fig
                ),
                dcc.Graph(
                    id='duration-distr',
                    figure=_duration_fig
                )
            ]
        ),
    ]

# html.Div(
#     style={
#         "display": "flex",
#         "width": "50%",
#         'alignItems': 'flex-start' 
#     },
#     children=[
#         dmc.Select(
#             id='duration-lane-select',
#             label='Choose Lane',
#             data=[
#                 {'value': 'safe', 'label': 'Safe Lane'},
#                 {'value': 'mid', 'label': 'Mid Lane'},
#                 {'value': 'off', 'label': 'Off lane'}
#             ],
#             w=300
#         ),
#         dmc.Select(
#             id='duration-sort-select',
#             label='Sort by',
#             data=[
#                 {'value': 'winrate', 'label': 'Win-rate'},
#                 {'value': 'count', 'label': 'Times played'}
#             ],
#             value='win',
#             w=300,
#             mb='md'
#         )
#     ]
# ),

@callback(
        Output('error-card', 'children'),
        Output('error-card', 'style'),
        Input('top-heroes', 'figure')
)
def show_error(figure):
    if figure == None:
        style={
                "display": "flex",
                "width": "100%",
                'alignItems': 'flex-start',
                'height': '100px'
        }
        paper = dmc.Paper(
            withBorder=True,
            p='lg',
            w=200,
            children=[
                dmc.Text('Error: either no games found or problem with query', size='xs', c='dimmed', fw=700, tt="uppercase"),
            ]
        )
        return paper, style
    else:
        style={
                "display": "flex",
                "width": "100%",
                'alignItems': 'flex-start',
                'height': '0px'
        }
        return [], style

@callback(
        Output('total-matches', 'children'),
        Output('stat-radiant-win', 'children'),
        Output('stat-avg-duration', 'children'),
        Output('top-heroes', 'figure'),
        Output('duration-distr', 'figure'),
        State('url', 'pathname'),
        Input('top-heroes-select', 'value'),
        *[Input(component_id, 'value') for component_id in FILTER_IDS.values()],
        prevent_initial_call=True
)
def update_overview(pathname, graph_select, *args):
    if pathname != '/':
        return no_update
    filters = {
        f.filter_name: ctx.inputs.get(f'{f.component_id}.value')
        for f in FILTERS
    }
    qb = QueryBuilder()
    qb = Filter.handle_filters(qb, **filters)
    query, params = qb.build(
        select='''
            COUNT(*),
        AVG(CAST("didRadiantWin" AS INT)),
        AVG("durationSeconds")
        '''
    )
    results = db.query_select(query, params=params)[0]
    found_matches = results[0]
    if found_matches == 0:
        return found_matches, 0, 0, None, None, None
    if len(results) == 0:
        return 0, 0, 0, None, None, None
    radiant_win = str(round(results[1], 2)) + '%'
    avg_game_length = convert_duration_format(results[2]) 
    try:
        match graph_select:
            case 'win':
                top_heroes_fig = fig_top_winrate(qb.copy(), found_matches)
            case 'pick':
                top_heroes_fig = fig_most_picked(qb.copy(), found_matches)
            case 'ban':
                top_heroes_fig = fig_most_banned(qb.copy(), found_matches)
            case 'pres':
                top_heroes_fig = fig_most_present(qb.copy(), found_matches)      
    except:
        top_heroes_fig = None
    duration_fig = fig_duration_hist(qb.copy())
    return found_matches, radiant_win, avg_game_length, top_heroes_fig, duration_fig 

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


