import pandas as pd
import numpy as np

from urllib.parse import urlencode, parse_qs 

import os
import sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project root (dota-project)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
# Get the src directory
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

# Add them to sys.path
sys.path.append(PROJECT_ROOT)
sys.path.append(SRC_DIR)
sys.path.append(CURRENT_DIR)

from db_functions import DotaDB
from app_functions import *

from dash import Dash, html, dcc, Input, Output, State, page_container, no_update, ctx
import dash_mantine_components as dmc

import logging
from basic_logger import setup_logger
import time

from theme import *
from dashboard.filters import *

db = DotaDB(schema='public')
setup_logger(logfile_path='logs/dashboard_app.log')
app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

server = app.server
app.layout = dmc.MantineProvider(
    theme=MANTINE_THEME,
    children=[
        dcc.Location(id='url', refresh=False), 
        dmc.AppShell(
            id='main-shell', 
            children=[
                dmc.AppShellHeader(
                    id='shell-header',
                    style={
                        "display": "flex",
                        'alignItems': 'center'
                    },
                    children=[
                        dmc.Tabs(
                            id='navigation-tabs',
                            children=[
                                dmc.TabsList(
                                    children=[
                                        dmc.Group(
                                            children=[
                                                # 1. BRANDING LINK (Removed width: 100%)
                                                dcc.Link(
                                                    dmc.Group([
                                                        dmc.Title('Dota 2 Analytics'),
                                                        dmc.Badge(id='header-badge')
                                                    ]),
                                                    id='banner-overview',
                                                    href='/',
                                                    style={
                                                        'textDecoration': 'none',
                                                        'color': 'inherit',
                                                        'marginRight': '40px' # Add some space before the tabs
                                                    }
                                                ),
                                                
                                                # 2. NAVIGATION TABS
                                                dcc.Link(
                                                    dmc.TabsTab('Overview', value='overview'),
                                                    id='navbar-overview',
                                                    href='/',
                                                    style={'textDecoration': 'none', 'color': 'inherit'}
                                                ),
                                                dcc.Link(
                                                    dmc.TabsTab('Find match', value='find-match'),
                                                    id='navbar-find-match',
                                                    href='/find-match?page=1',
                                                    style={'textDecoration': 'none', 'color': 'inherit'}
                                                ),
                                            ],
                                            justify='flex-start',
                                            gap="xl", # Mantine way to add spacing between items
                                            ml=20
                                        )
                                    ]
                                )
                            ],
                            variant='pills'
                        ) 
                    ]
                ),
                dmc.AppShellNavbar(
                    id='shell-navbar',
                    children=[]
                ),
                dmc.AppShellMain(id='page-content', children=[page_container], style={'width': '100%'})
            ],
            header={'height': 60},
            padding='md'
        )           
    ]
)

#Keeps search bar
@app.callback(
        Output('banner-overview', 'href'),
        Output('navbar-overview', 'href'),
        Output('navbar-find-match', 'href'),
        Input('url', 'search')
)
def update_nav_links(search):
    search = search or ''
    return f'/{search}', f'/{search}', f'/find-match{search}'

@app.callback(
        Output('navigation-tabs', 'value'),
        Input('url', 'pathname')
)
def set_tab(pathname):
    if pathname == '/':
        return 'overview'
    elif pathname == '/find-match':
        return 'find-match'

@app.callback(
        Output(component_id='header-badge', component_property='children'),
        Input('url', 'pathname')
)
def update_logo(pathname:str):
    if pathname.startswith('/match/'):
        match_id = pathname.split('/')[-1]
        return f'Match ID {match_id}'
    else:
        total_matches = get_total_matches()
        return f'{total_matches} matches found'

@app.callback(
    Output('main-shell', 'navbar'),
    Input('url', 'pathname')
)
def toggle_navbar_visibility(pathname: str):
    # Only show the sidebar width if we are on the find-match page
    if pathname in ['/', '/find-match']:
        return {'width': 300, 'breakpoint': 'sm', 'collapsed': {'mobile': True, 'desktop': False}}
    return {'width': 0, 'collapsed': {'mobile': True, 'desktop': True}}

@app.callback(
        Output('patch-filter', 'data'),
        Output('league-filter', 'data'),
        Output('teams-filter', 'placeholder'),
        Output('teams-filter', 'data'),
        Output('date-filter', 'minDate'),
        Output('date-filter', 'maxDate'),
        Output('date-filter', 'defaultDate'),
        *[Input(component_id, 'value') for component_id in FILTER_IDS.values()],
        prevent_initial_call=True
)
def update_filter_state(*args):
    triggered = ctx.triggered_id
    filters = {
        f.filter_name: ctx.inputs.get(f'{f.component_id}.value')
        for f in FILTERS
    }

    data = []
    for f in FILTERS:
        if f.filter_name != 'durations':
            data.extend(f.get_outputs(triggered, **filters))
    return tuple(data)

@app.callback(
    Output("url", "search", allow_duplicate=True),
    State('url', 'pathname'),
    *[Input(component_id, 'value') for component_id in FILTER_IDS.values()],
    prevent_initial_call=True
)
def update_url_from_filters_overview(pathname, *args): #TODO: create a helper function from this and the one below
    if pathname != '/':
        return no_update
    params = {}
    filters = {}
    for filter_name, component_id in FILTER_IDS.items():
        filter_value = ctx.inputs.get(f'{component_id}.value')
        filters[filter_name] = filter_value
    params = update_url_from_filters_helper({}, filters)
    return f"?{urlencode(params, doseq=True)}" if params else ""

@app.callback(
    Output("url", "search", allow_duplicate=True),
    State('url', 'pathname'),
    Input('match-pagination', 'value'),
    *[Input(component_id, 'value') for component_id in FILTER_IDS.values()],
    prevent_initial_call=True
)
def update_url_from_filters_find_match(pathname, page_number, *args):
    if pathname != '/find-match':
        return no_update
    params = {}
    if page_number: params['page'] = page_number
    filters = {}
    for filter_name, component_id in FILTER_IDS.items():
        filter_value = ctx.inputs.get(f'{component_id}.value')
        filters[filter_name] = filter_value
    params = update_url_from_filters_helper(params, filters)
    return f"?{urlencode(params, doseq=True)}" if params else ""

@app.callback(
    Output('shell-navbar', 'children'),
    Input('url', 'pathname'),
    State('url', 'search')
)
def sync_sidebar_from_url(pathname, search):
    if pathname not in ['/find-match', '/']:
        return no_update
    params = parse_qs(search.lstrip('?'))

    filters = {
        f.filter_name: f.parse_from_url(params)
        for f in FILTERS
    }
    components = [
        f.render(
            value=filters[f.filter_name],
            data=f.get_data(**filters)
        )
        for f in FILTERS
    ]
    return dmc.ScrollArea(p="md", children=components)

if __name__ == '__main__':
    app.run(debug=True)