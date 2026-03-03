import pandas as pd
import numpy as np

from urllib.parse import parse_qs

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

from dash import Dash, html, dcc, Input, Output, clientside_callback, page_container
import dash_mantine_components as dmc

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
from pages.find_match import set_min_date, set_max_date
server = app.server
app.layout = dmc.MantineProvider(
    theme={'colorScheme': 'dark', 'primaryColor': 'indigo'},
    children=[
        dcc.Location(id='url', refresh=False),
        dmc.Container( 
            children=[
                dmc.AppShell(
                    id='main-shell', 
                    children=[
                        dmc.AppShellHeader(
                            id='shell-header',
                            children=[]
                        ),
                        dmc.AppShellNavbar(
                            id='shell-navbar',
                            children=[]
                        ),
                        dmc.AppShellMain(id='page-content', children=[page_container])
                    ],
                    header={'height': 60},
                    padding='md'
                )           
            ]
        )
    ]  
)

def render_sidebar(saved_league=None, saved_start=None, saved_end=None):
    return dmc.ScrollArea(
        offsetScrollbars=True,
        children=[
            dmc.Select(
                id='league-filter',
                label='League',
                data=get_leagues(),
                value=saved_league,
                searchable=True
            ),
            dmc.DatePicker(
                id='date-filter',
                type='range',
                minDate=set_min_date(), # You may need to update these to handle 'None' safely
                maxDate=set_max_date(),
                value=[saved_start, saved_end],
                mt="md"
            )
        ]
    )

@app.callback(
    Output('shell-header', 'children'),
    Output('shell-navbar', 'children'), # <--- Put filters here
    Output('main-shell', 'navbar'),
    Input('url', 'pathname'),
    Input('url', 'search') # Listen for URL params to keep filters in sync
)
def update_shell_ui(pathname, search):
    # 1. Default Header Content
    header_content = dmc.Group([dmc.Title('Dota 2 Analytics')], justify='center')
    
    # 2. Handle Find Match Page (With Sidebar)
    if pathname == '/find-match':
        # Parse URL to keep sidebar inputs synced if user refreshes
        params = parse_qs(search.lstrip('?'))
        sidebar = render_sidebar(
            saved_league=params.get('league', [None])[0],
            saved_start=params.get('startDate', [None])[0],
            saved_end=params.get('endDate', [None])[0]
        )
        navbar_config = {'width': 300, 'breakpoint': 'sm', 'collapsed': {'mobile': True, 'desktop': False}}
        return header_content, sidebar, navbar_config

    # 3. Handle Match Detail Page (No Sidebar)
    elif pathname.startswith('/match/'):
        match_id = pathname.split('/')[-1]
        header_content = dmc.Group([dmc.Title(f'Match {match_id}')], justify='center')
        
    # 4. Fallback (Overview / Home)
    navbar_config = {'width': 0, 'collapsed': {'mobile': True, 'desktop': True}}
    return header_content, None, navbar_config

clientside_callback(
    """
    function(pathname) {
        if (pathname === '/' || pathname === '') {
            return '/overview';
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('url', 'pathname'),
    Input('url', 'pathname')
)
    
if __name__ == '__main__':
    app.run(debug=True)