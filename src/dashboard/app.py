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

from dash import Dash, html, dcc, Input, Output, State, page_container, no_update
import dash_mantine_components as dmc
from flask import redirect, request

db = DotaDB(schema='public')
app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

server = app.server
app.layout = dmc.MantineProvider(
    theme={'colorScheme': 'dark', 'primaryColor': 'indigo'},
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
                            children=[
                                dmc.TabsList(
                                    children=[
                                        dmc.Group(
                                            children=[
                                                # 1. BRANDING LINK (Removed width: 100%)
                                                dcc.Link(
                                                    dmc.Group([
                                                        dmc.Title('Dota 2 Analytics'),
                                                        dmc.Badge(id='header-badge', variant='gradient')
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
                                                    href='/find-match',
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
        Output(component_id='header-badge', component_property='children'),
        Input('url', 'pathname')
)
def update_logo(pathname:str):
    if pathname.startswith('/match/'):
        match_id = pathname.split('/')[-1]
        return f'Match ID {match_id}'
    else:
        return f'{get_total_matches()} matches found'

@app.callback(
    Output('main-shell', 'navbar'),
    Input('url', 'pathname')
)
def toggle_navbar_visibility(pathname: str):
    # Only show the sidebar width if we are on the find-match page
    if pathname.startswith('/find-match') or pathname.startswith('/'):
        return {'width': 300, 'breakpoint': 'sm', 'collapsed': {'mobile': True, 'desktop': False}}
    return {'width': 0, 'collapsed': {'mobile': True, 'desktop': True}}

@app.callback(
        Output(component_id='date-filter', component_property='minDate'),
        Input(component_id='league-filter', component_property='value')
)
def set_min_date(league=None):
    return get_date_boundary('MIN', league)

@app.callback(
        Output(component_id='date-filter', component_property='maxDate'),
        Input(component_id='league-filter', component_property='value')
)
def set_max_date(league=None):
    return get_date_boundary('MAX', league)

@app.callback( #TODO: Merge the above callbacks and this to one, add a helper function that deals with all the logic of updating filters
        Output('league-filter', 'data'),
        Input('date-filter', 'value')
)
def set_leagues(dates):
    return get_leagues(dates)

@app.callback(
    Output("url", "search"),
    State('url', 'pathname'),
    Input("league-filter", "value"),
    Input("date-filter", "value"),
    prevent_initial_call=True
)
def update_url_from_filters(pathname, league, dates):
    if pathname in ['/find-match', '/']:
        params = {}
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
        saved_league = params.get('league', [None])[0]
        saved_start = params.get('startDate', [None])[0]
        saved_end = params.get('endDate', [None])[0]
        dates = [saved_start, saved_end]  
        # Return the Mantine components directly to the 'shell-navbar' in app.py
        return dmc.ScrollArea(
            p="md",
            children=[
                dmc.Select(
                    id='league-filter',
                    label='League',
                    data=get_leagues(dates),
                    value=saved_league,
                    searchable=True
                ),
                dmc.DatePicker(
                    id='date-filter',
                    type='range',
                    minDate=get_date_boundary('MIN', saved_league),
                    maxDate=get_date_boundary('MAX', saved_league),
                    value=dates,
                    # defaultDate=saved_start,
                    mt="md"
                )
            ]
        )
    return no_update

if __name__ == '__main__':
    app.run(debug=True)