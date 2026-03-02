import pandas as pd
import numpy as np

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

from dash import Dash, html, dcc, Input, Output, State, callback
import dash_mantine_components as dmc

app = Dash(__name__)
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
                        dmc.AppShellMain(id='page-content', children=[])
                    ],
                    header={'height': 60},
                    padding='md'
                )           
            ]
        )
    ]  
)
    
if __name__ == '__main__':
    app.run(debug=True)