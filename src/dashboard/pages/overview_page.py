import dash
from dash import html, callback, Input, Output, State, no_update
import dash_mantine_components as dmc

from app_functions import *

dash.register_page(__name__, path='')

def layout():
    return dmc.Container(
        children=[
            dmc.ScrollArea(
                children=[
                    dmc.Text('overview')
                ]
            )
        ]
    )