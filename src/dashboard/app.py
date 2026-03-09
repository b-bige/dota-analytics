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
                                                    href='/',
                                                    style={'textDecoration': 'none', 'color': 'inherit'}
                                                ),
                                                dcc.Link(
                                                    dmc.TabsTab('Find match', value='find-match'),
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
        Output('date-filter', 'defaultDate'),
        Output('date-filter', 'minDate'),
        Output('date-filter', 'maxDate'),
        Input('patch-filter', 'value'),
        Input('league-filter', 'value'),
        Input('date-filter', 'value'),
        prevent_initial_call=True
)
def update_filter_state(patch, league, dates):
    triggered = ctx.triggered_id
    filters = dict(patch=patch, league=league, dates=dates)

    patch_data  = no_update if triggered == 'patch-filter'  else get_patches(**filters, exclude='patch')
    league_data = no_update if triggered == 'league-filter' else get_leagues(**filters, exclude='league')

    min_date     = get_date_boundary('MIN', **filters, exclude='dates')
    max_date     = get_date_boundary('MAX', **filters, exclude='dates')
    default_date = min_date
    return patch_data, league_data, default_date, min_date, max_date

@app.callback(
    Output("url", "search"),
    State('url', 'pathname'),
    Input('patch-filter', 'value'),
    Input("league-filter", "value"),
    Input("date-filter", "value"),
    prevent_initial_call=True
)
def update_url_from_filters(pathname, patch, league, dates):
    if pathname in ['/find-match', '/']:
        params = {}
        if patch: params['patch'] = patch
        if league: params["league"] = league
        if dates:
            if dates[0]: params["startDate"] = dates[0]
            if dates[1]: params["endDate"] = dates[1]
        return f"?{urlencode(params)}" if params else ""
    return no_update

@app.callback(
    Output("url", "search", allow_duplicate=True),
    State('url', 'pathname'),
    Input('match-pagination', 'value'),
    State("league-filter", "value"),
    State("date-filter", "value"),
    prevent_initial_call=True
)
def update_url_from_pagination(pathname, page_number, league, dates):
    if pathname == '/find-match':
        params = {}
        if page_number: params["page"] = page_number
        if league: params["league"] = league
        if dates:
            if dates[0]: params["startDate"] = dates[0]
            if dates[1]: params["endDate"] = dates[1]
        return f"?{urlencode(params)}" if params else ""
    return no_update

@app.callback(
    Output('shell-navbar', 'children'),
    Input('url', 'pathname'),
    State('url', 'search')
)
def sync_sidebar_from_url(pathname, search):
    if pathname in ['/find-match', '/']:
        params = parse_qs(search.lstrip('?'))
        # Extract saved values
        patch = params.get('patch', [None])[0]
        league = params.get('league', [None])[0]
        start_date = params.get('startDate', [None])[0]
        end_date = params.get('endDate', [None])[0]
        dates = [start_date, end_date]  
        # Return the Mantine components directly to the 'shell-navbar' in app.py
        patch_data, league_data, min_date, max_date = get_url_data(patch=patch, league=league, dates=dates)
        return dmc.ScrollArea(
            p="md",
            children=[
                dmc.Select(
                    id='patch-filter',
                    label='Game Version',
                    data=patch_data,
                    value=patch,
                    searchable=True
                ),
                dmc.Select(
                    id='league-filter',
                    label='League',
                    data=league_data,
                    value=league,
                    searchable=True
                ),
                dmc.DatePicker(
                    id='date-filter',
                    type='range',
                    minDate=min_date,
                    maxDate=max_date,
                    value=dates,
                    defaultDate=start_date if start_date else None,
                    mt="md"
                )
            ]
        )
    return no_update

if __name__ == '__main__':
    app.run(debug=True)