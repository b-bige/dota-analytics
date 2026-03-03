import dash
from dash import html
import dash_mantine_components as dmc

from app_functions import *

dash.register_page(__name__, path='/overview')

def layout():
    return dmc.Container(
        children=[
            dmc.Text('overview page', size=60)
        ]
    )