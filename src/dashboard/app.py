import pandas as pd
import numpy as np

import os
import sys
sys.path.append(os.path.abspath('./src/dashboard'))
sys.path.append(os.path.abspath('./src'))

from db_functions import DotaDB
from app_functions import *

from dash import Dash, html, dcc, Input, Output, State, callback
import dash_mantine_components as dmc

app = Dash()
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