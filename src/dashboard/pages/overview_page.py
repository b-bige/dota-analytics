import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import parse_qs

import time
import logging
logger = logging.getLogger(__name__)

from theme import PLOTLY_COLORSCALES, COLORS

from app_functions import *
from dashboard.filters import *

dash.register_page(__name__, path='')

_total_matches = get_total_matches()
_winrate_fig = fig_top_winrate(QueryBuilder(), _total_matches)
_duration_fig = fig_duration_hist(QueryBuilder())

def layout(**kwargs):
    return dmc.Tabs(
        id='analysis-navigation-tabs',
        value=kwargs['tab'], 
        variant='pills',
        children=[
            dmc.TabsList(
                children=[
                    dmc.Group(
                        children=[
                            dmc.TabsTab('Overview', value='overview'),
                            dmc.TabsTab('Meta analysis', value='meta'),
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
    # Input('top-heroes-select', 'value'),
    *[Input(component_id, 'value') for component_id in FILTER_IDS.values()]
)
def render_tab_content(search, graph_select, *args):
    params = parse_qs(search.lstrip('?')) if search else {}
    active_tab = params.get('tab', ['overview'])[0]
    filters = {
        f.filter_name: ctx.inputs.get(f'{f.component_id}.value')
        for f in FILTERS
    }
    qb = QueryBuilder()
    qb = Filter.handle_filters(qb, **filters)
    has_filters = len(params.keys()) != 1
    if active_tab == 'overview':
        return render_overview_layout(qb, filters, graph_select, has_filters), active_tab
    if active_tab == 'meta': 
        return render_meta_layout(qb, filters, has_filters), active_tab
    if active_tab == 'economy':
        return render_economy_layout(qb, filters, has_filters), active_tab
    
def render_overview_layout(qb: QueryBuilder, filters: dict, graph_select, has_filters: bool):
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
        return html.Div(
            id='error-card',
            style={
                "display": "flex",
                "width": "100%",
                'alignItems': 'flex-start',
                'height': '100px',
            },
            children=[
                dmc.Paper(
                    withBorder=True,
                    p='lg',
                    w=200,
                    children=[
                        dmc.Text('Error: either no games found or problem with query', size='xs', c='dimmed', fw=700, tt="uppercase"),
                    ]
                )
            ]
        ),
    radiant_win = str(round(results[1], 2)) + '%'
    avg_game_length = convert_duration_format(results[2]) 
    query, params = qb.build(select='AVG(radiant_score + dire_score)')
    avg_kills = round(db.query_select(query, params=params)[0][0], 0)
    if not graph_select:
        graph_select = 'win'
    if has_filters:
        try:
            duration_fig = fig_duration_hist(qb.copy())
            if filters['heroes']:
                query, params = qb.build('md.id')
                ids = [r[0] for r in db.query_select(query, params=params)]
                qb_heroes = QueryBuilder()
                qb_heroes.where('md.id = ANY(%s)', ids)
                qb_heroes = Filter.handle_filters(qb_heroes, **filters, exclude='heroes')
            else:
                qb_heroes = qb.copy()
            match graph_select:
                case 'win':
                    top_heroes_fig = fig_top_winrate(qb_heroes.copy(), found_matches)
                case 'pick':
                    top_heroes_fig = fig_most_picked(qb_heroes.copy(), found_matches)
                case 'ban':
                    top_heroes_fig = fig_most_banned(qb_heroes.copy(), found_matches)
                case 'pres':
                    top_heroes_fig = fig_most_present(qb_heroes.copy(), found_matches)      
        except:
            top_heroes_fig = None    
            duration_fig = None
    else:
        top_heroes_fig = _winrate_fig
        duration_fig = _duration_fig 
    return [
        html.Div(
            style={
                "display": "flex",
                "width": "100%",
                "justifyContent": "space-evenly",
                'marginBottom': 20
            },
            children=[
                stat_card("Total Matches", id="total-matches", value=found_matches),
                stat_card("Win Rate (Radiant)", id="stat-radiant-win", value=radiant_win),
                stat_card("Avg Game Length", id="stat-avg-duration", value=avg_game_length),
                stat_card("Avg Kills", id='stat-avg-kills', value=avg_kills)
            ]
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
        dmc.SimpleGrid(
            cols={"base": 1, "lg": 2}, # 1 column on small screens, 2 on large
            spacing="xl",
            mt="md",
            children=[
                dmc.LoadingOverlay(
                    visible=False,
                    id="loading-overlay",
                    overlayProps={"radius": "sm", "blur": 2},
                    zIndex=10,
                ),
                dcc.Graph(
                    id='top-heroes',
                    figure=top_heroes_fig,
                    responsive=True, # Crucial: tells Plotly to listen for resize events
                    style={"width": "100%"}
                ),
                dcc.Graph(
                    id='duration-distr',
                    figure=duration_fig,
                    responsive=True,
                    style={"width": "100%"}
                )
            ]
        )
    ]

def render_meta_layout(qb: QueryBuilder, filters: dict, has_filters: bool):
    return html.Div('Under development')
    
def render_economy_layout(qb: QueryBuilder, filters: dict, has_filters: bool):
    return html.Div('Coming soon')

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

# @callback(
#         Output('total-matches', 'children'),
#         Output('stat-radiant-win', 'children'),
#         Output('stat-avg-duration', 'children'),
#         Output('stat-avg-kills', 'children'),
#         Output('top-heroes', 'figure'),
#         Output('duration-distr', 'figure'),
#         Input('analysis-navigation-tabs', 'value'),
#         State('url', 'pathname'),
#         Input('top-heroes-select', 'value'),
#         *[Input(component_id, 'value') for component_id in FILTER_IDS.values()],
#         prevent_initial_call=True
# )
# def update_overview(active_tab, pathname, graph_select, *args):
#     if pathname != '/':
#         return no_update
#     filters = {
#         f.filter_name: ctx.inputs.get(f'{f.component_id}.value')
#         for f in FILTERS
#     }
#     qb = QueryBuilder()
#     qb = Filter.handle_filters(qb, **filters)
#     query, params = qb.build(
#         select='''
#             COUNT(*),
#         AVG(CAST("didRadiantWin" AS INT)),
#         AVG("durationSeconds")
#         '''
#     )
#     results = db.query_select(query, params=params)[0]
#     found_matches = results[0]
#     if found_matches == 0:
#         return found_matches, 0, 0, None, None, None
#     if len(results) == 0:
#         return 0, 0, 0, None, None, None
#     radiant_win = str(round(results[1], 2)) + '%'
#     avg_game_length = convert_duration_format(results[2]) 
#     query, params = qb.build(select='AVG(radiant_score + dire_score)')
#     avg_kills = round(db.query_select(query, params=params)[0][0], 0)
#     try:
#         if filters['heroes']:
#             query, params = qb.build('md.id')
#             ids = [r[0] for r in db.query_select(query, params=params)]
#             qb_heroes = QueryBuilder()
#             qb_heroes.where('md.id = ANY(%s)', ids)
#             qb_heroes = Filter.handle_filters(qb_heroes, **filters, exclude='heroes')
#         else:
#             qb_heroes = qb.copy()
#         match graph_select:
#             case 'win':
#                 top_heroes_fig = fig_top_winrate(qb_heroes.copy(), found_matches)
#             case 'pick':
#                 top_heroes_fig = fig_most_picked(qb_heroes.copy(), found_matches)
#             case 'ban':
#                 top_heroes_fig = fig_most_banned(qb_heroes.copy(), found_matches)
#             case 'pres':
#                 top_heroes_fig = fig_most_present(qb_heroes.copy(), found_matches)      
#     except:
#         top_heroes_fig = None
#     duration_fig = fig_duration_hist(qb.copy())
#     return found_matches, radiant_win, avg_game_length, avg_kills, top_heroes_fig, duration_fig 

def stat_card(label, id, value):
    return dmc.Paper(
        withBorder=True,
        p='lg',
        w=200,
        children=[
            dmc.Text(label, size='xs', c='dimmed', fw=700, tt="uppercase"),
            dmc.Title(value, id=id, order=2)
        ]
    )


