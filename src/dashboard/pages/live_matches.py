import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

import time
import logging

from theme import PLOTLY_COLORSCALES, COLORS

from app_functions import *
from dashboard.filters import *

dash.register_page(__name__, path='/live-matches')

def layout(page=1, league=None, startDate=None, endDate=None, **kwargs):
    return dmc.Container(
        children=[ 
            dmc.ScrollArea(
                h=600, # Fixed height helps with ScrollArea behavior
                offsetScrollbars=True,
                children=[
                    dmc.SimpleGrid(
                        id='match-container', 
                        cols=2,        # Force 2 items per row
                        spacing="md",  # Gap between cards,
                        mt=10,
                        children=[]
                    )
                ]
            ),
            dmc.Space(h="md"),
            dmc.Group(
                justify="center",
                children=[
                    dmc.Pagination(
                        id='match-pagination',
                        total=0, 
                        value=int(page),
                        radius="sm",
                        withEdges=True,
                    )
                ]
            )
        ]
    )