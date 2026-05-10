import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx, ALL
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import parse_qs

import time
import logging
logger = logging.getLogger(__name__)

from src.dashboard.theme import PLOTLY_COLORSCALES, COLORS

from src.dashboard.app_functions import *
from src.dashboard.filters import *
from src.dashboard import db_manager
from src.dashboard.query_builder import QueryBuilder
from src.dashboard.data_assets import HERO_DICT, HERO_LIST

dash.register_page(__name__, path='')

def layout(**kwargs):
    return dmc.Tabs(
        id='analysis-navigation-tabs',
        value=kwargs.get('tab', 'overview'), 
        variant='pills',
        children=[
            dmc.TabsList(
                children=[
                    dmc.Group(
                        children=[
                            dmc.TabsTab('Overview', value='overview'),
                            # dmc.TabsTab('Meta analysis', value='meta'), TODO
                            dmc.TabsTab('Economy analysis', value='economy'),
                        ]
                    )
                ]
            ),
            html.Div(id="tabs-content-container", style={"marginTop": "20px"}, children=[])
        ]
    )

@callback(
    Output('tabs-content-container', 'children'),
    Output('analysis-navigation-tabs', 'value'),
    Input('url', 'search'),
)
def render_tab_content(search):
    params = parse_qs(search.lstrip('?')) if search else {}
    active_tab = params.get('tab', ['overview'])[0]
    if active_tab == 'overview':
        return render_overview_layout(), active_tab
    if active_tab == 'meta': 
        return render_meta_layout(), active_tab
    if active_tab == 'economy':
        return render_economy_layout(), active_tab
    
def render_overview_layout():
    return [
        dcc.Loading(
            html.Div(
                id="overview-stats-container", 
                style={
                    "display": "flex",
                    "width": "100%",
                    "minHeight": "90px",           # Matches the height of your cards
                    "height": "90px",              # Enforces the exact vertical space
                    "justifyContent": "space-evenly",
                    "alignItems": "center",        # Centers the loading spinner vertically
                    "marginBottom": 20,
                    "backgroundColor": "transparent",
                }
            ),
            type="circle",
            color=COLORS['primary']
        ),
        html.Div(
            style={"display": "flex", "width": "100%", 'alignItems': 'flex-start'},
            children=[
                dmc.Select(
                    id={'type': 'dynamic-select', 'index': 'top-heroes-select'},
                    label='Top heroes by',
                    data=[
                        {'value': 'win', 'label': 'Win-rate'},
                        {'value': 'pick', 'label': 'Pick-rate'},
                        {'value': 'ban', 'label': 'Ban-rate'},
                        {'value': 'pres', 'label': 'Presence-rate (Pick & Ban)'}
                    ],
                    value='win',
                    w=300,
                    mb='md',
                    persistence=True,     
                    persistence_type='session'
                ),
            ]
        ),
        dmc.SimpleGrid(
            cols={"base": 1, "lg": 2},
            spacing="xl",
            mt="md",
            children=[
                dcc.Loading(
                    dcc.Graph(
                        id='top-heroes-graph', 
                        responsive=True,
                        style={"width": "100%"}
                    ),
                    type="dot",
                    color=COLORS['primary']
                ),
                dcc.Loading(
                    dcc.Graph(
                        id='duration-distr-graph', 
                        responsive=True,
                        style={"width": "100%"}
                    ),
                    type="dot",
                    color=COLORS['primary']
                )
            ]
        )
    ]

def render_meta_layout():
    return html.Div('Under development')
    
def render_economy_layout():
    return [
        dmc.Grid(
            id='economy-layout-grid',
            children=[
                dmc.GridCol(
                    span=3,
                    children=[
                        dmc.MultiSelect(
                            id={'type': 'dynamic-select', 'index': 'gpm-heroes-select'},
                            label='Heroes',
                            placeholder='Select Heroes for Analysis',
                            data=list(HERO_LIST),
                            value=['Abaddon'],
                            maxValues=10,
                            persistence=True,     
                            persistence_type='session',
                            w='100%',
                            style={'flex': '1'}
                        )
                    ]
                ),
                dmc.GridCol(
                    span=3,
                    children=[]
                ),
                dmc.GridCol(
                    span=3,
                    children=[
                        dmc.Select(
                            id={'type': 'dynamic-select', 'index': 'position-select'},
                            label='Role',
                            placeholder='Select Role for Analysis',
                            data=['Carry', 'Midlaner', 'Offlaner', 'Roamer/Soft Support', 'Hard Support'],
                            value='Carry',
                            persistence=True,
                            persistence_type='session',
                            w='100%',
                            style={'flex': '1'}
                        )
                    ]
                )
            ]
        ),
        dmc.SimpleGrid(
            id='economy-graph-grid',
            cols={"base": 1, "lg": 2},
            children=[
                dcc.Loading(
                    dcc.Graph(
                        id='gpm-volatility-graph',
                        responsive=True,
                        style={"width": "100%"}
                    ) 
                ),
                dcc.Loading(
                    dcc.Graph(
                        id='greed-winrate-graph',
                        responsive=True,
                        style={"width": "100%"},
                    ) 
                )
            ]
        ),
    ]

@callback(
    Output('overview-stats-container', 'children'),
    *[Input(component_id, 'value') for component_id in FILTER_IDS.values()],
)
def update_overview_kpis(*filter_args):
    qb = QueryBuilder()
    filters = {f.filter_name: val for f, val in zip(FILTERS, filter_args)}
    qb = Filter.handle_filters(qb, **filters)
    
    query, params = qb.build(select='COUNT(*), AVG(CAST("didRadiantWin" AS INT)), AVG("durationSeconds")')
    results = db_manager.select(query, params=params)[0]
    
    found_matches = results[0]
    if found_matches == 0:
        return [dmc.Text("No games found for these filters.", c='red', fw=700)]
        
    radiant_win = str(round(results[1], 2)) + '%' if results[1] else '0%'
    avg_game_length = convert_duration_format(results[2])
    
    query, params = qb.build(select='AVG(radiant_score + dire_score)')
    avg_kills = round(db_manager.select(query, params=params)[0][0] or 0, 0)

    return [
        stat_card("Total Matches", id="total-matches", value=found_matches),
        stat_card("Win Rate (Radiant)", id="stat-radiant-win", value=radiant_win),
        stat_card("Avg Game Length", id="stat-avg-duration", value=avg_game_length),
        stat_card("Avg Kills", id='stat-avg-kills', value=avg_kills)
    ]

@callback(
    Output('top-heroes-graph', 'figure'),
    Input({'type': 'dynamic-select', 'index': 'top-heroes-select'}, 'value'),
    *[Input(component_id, 'value') for component_id in FILTER_IDS.values()],
)
def update_top_heroes_graph(graph_select, *filter_args):
    qb = QueryBuilder()
    filters = {f.filter_name: val for f, val in zip(FILTERS, filter_args)}
    qb = Filter.handle_filters(qb, **filters)
    
    count_query, count_params = qb.build(select='COUNT(*)')
    found_matches = db_manager.select(count_query, params=count_params)[0][0]
    
    if found_matches == 0:
        return no_update 

    if filters.get('heroes'):
        query, params = qb.build('md.id')
        ids = [r[0] for r in db_manager.select(query, params=params)]
        qb_heroes = QueryBuilder()
        qb_heroes.where('md.id = ANY(:ids)', {'ids': ids})
        qb_heroes = Filter.handle_filters(qb_heroes, **filters, exclude='heroes')
    else:
        qb_heroes = qb.copy()

    match graph_select:
        case 'win': return fig_top_winrate(qb_heroes, found_matches)
        case 'pick': return fig_most_picked(qb_heroes, found_matches)
        case 'ban': return fig_most_banned(qb_heroes, found_matches)
        case 'pres': return fig_most_present(qb_heroes, found_matches)
        case _: return fig_top_winrate(qb_heroes, found_matches)

@callback(
    Output('duration-distr-graph', 'figure'),
    *[Input(component_id, 'value') for component_id in FILTER_IDS.values()],
)
def update_duration_graph(*filter_args):
    qb = QueryBuilder()
    filters = {f.filter_name: val for f, val in zip(FILTERS, filter_args)}
    qb = Filter.handle_filters(qb, **filters)
    return fig_duration_hist(qb)

@callback(
    Output('gpm-volatility-graph', 'figure'),
    Input({'type': 'dynamic-select', 'index': 'gpm-heroes-select'}, 'value'),
    *[Input(component_id, 'value') for component_id in FILTER_IDS.values()],
)
def update_gpm_volatility(selected_heroes, *filter_args):
    qb = QueryBuilder()
    filters = {f.filter_name: val for f, val in zip(FILTERS, filter_args)}
    qb = Filter.handle_filters(qb, **filters)
    fig = fig_gpm_volatility(qb, selected_heroes)
    return fig

@callback(
    Output('greed-winrate-graph', 'figure'),
    Input({'type': 'dynamic-select', 'index': 'position-select'}, 'value'),
    *[Input(component_id, 'value') for component_id in FILTER_IDS.values()],
)
def update_greed_winrate(selected_position, *filter_args):
    qb = QueryBuilder()
    filters = {f.filter_name: val for f, val in zip(FILTERS, filter_args)}
    qb = Filter.handle_filters(qb, **filters)
    
    return fig_greed_plot(qb, selected_position)

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

def stat_card(label, id, value):
    return dmc.Paper(
        withBorder=True,
        p='lg',
        w=200,
        h=90,
        children=[
            dmc.Text(label, size='xs', c='dimmed', fw=700, tt="uppercase"),
            dmc.Title(value, id=id, order=2)
        ]
    )