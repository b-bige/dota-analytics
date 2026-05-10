import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go
from zoneinfo import ZoneInfo
import numpy as np
from operator import itemgetter

import time
import logging
logger = logging.getLogger(__name__)

from src.dashboard.theme import PLOTLY_COLORSCALES, COLORS
from src.dashboard import db_manager
from src.analytics import DraftService
from src.dashboard.data_assets import HERO_LIST, HERO_DICT, PATCH_LIST, PATCH_DICT

dash.register_page(__name__, path='/draft-analysis')

draft_service = DraftService(db=db_manager)

def layout():
    """
    This page is an experimental page to manually analyze the draft service 
    and make it easier to make adjustments to it later on
    """
    return dmc.Container(
        size='lg', 
        children=[
            dmc.Select(
                id='patch-select',
                label='Patch',
                placeholder='Select Patch for match',
                data=PATCH_LIST,
                persistence=True,
                persistence_type='session',
                searchable=True
            ),
            html.Div(id='error-container'),
            dmc.SimpleGrid(
                cols=2,
                mt="xl",
                children=[
                    dmc.Paper(
                        p="md", withBorder=True, radius="md",
                        children=[
                            dmc.Title('Radiant', order=4, c=COLORS['radiant'], mb='sm'),
                            dmc.MultiSelect(
                                id='radiant-team-select',
                                label='Radiant team',
                                placeholder='Select 5 Heroes for the Radiant team',
                                data=list(HERO_LIST),
                                maxValues=5,
                                persistence=True,
                                persistence_type='session',
                                searchable=True
                            ),
                            dcc.Loading(
                                dmc.Title(id='radiant-score', children='Score: 0.5', order=3, mt="md", ta="center")
                            )
                        ]
                    ),
                    dmc.Paper(
                        p="md", withBorder=True, radius="md",
                        children=[
                            dmc.Title('Dire', order=4, c=COLORS['dire'], mb='sm'),
                            dmc.MultiSelect(
                                id='dire-team-select',
                                label='Dire team',
                                placeholder='Select 5 Heroes for the Dire team',
                                data=list(HERO_LIST),
                                maxValues=5,
                                persistence=True,
                                persistence_type='session',
                                searchable=True
                            ),
                            dcc.Loading(
                                dmc.Text(id='dire-score', children='Score: 0.5', fw=700, size="xl", mt="md", ta="center")
                            )
                        ]
                    ),
                ]
            ),
            dcc.Loading(
                dmc.Stack(
                    mt='xl',
                    gap='xs',
                    children=[
                        dmc.Text("Win Probability Distribution", ta="center", size="sm", fw=500, c="dimmed"),
                        dmc.ProgressRoot(
                            size=30,
                            radius="xl",
                            children=[
                                dmc.ProgressSection(
                                    id="radiant-progress",
                                    value=50, 
                                    color=COLORS['radiant'],
                                    children=[dmc.ProgressLabel(id="radiant-label", children="50%")]
                                ),
                                dmc.ProgressSection(
                                    id="dire-progress",
                                    value=50, 
                                    color=COLORS['dire'],
                                    children=[dmc.ProgressLabel(id="dire-label", children="50%")]
                                ),
                            ]
                        )
                    ]
                )
            )
        ]
    )

@callback(
    Output('error-container', 'children'),
    Output(component_id='radiant-score', component_property='children'),
    Output(component_id='dire-score', component_property='children'),
    Output(component_id='radiant-progress', component_property='value'),
    Output(component_id='radiant-label', component_property='children'),
    Output(component_id='dire-progress', component_property='value'),
    Output(component_id='dire-label', component_property='children'),
    Input(component_id='radiant-team-select', component_property='value'),
    Input(component_id='dire-team-select', component_property='value'),
    Input(component_id='patch-select', component_property='value'),
    prevent_initial_call=True
)
def calculate_draft_score(radiant_team, dire_team, patch_name):
    if not radiant_team or not dire_team or not patch_name:
        raise PreventUpdate
    if len(radiant_team) != 5 or len(dire_team) != 5:
        raise PreventUpdate
    duplicates = set(radiant_team) & set(dire_team)
    if duplicates:
        error_msg = dmc.Alert(
            f'Invalid Draft: {', '.join(duplicates)} cannot be on both teams.',
            title="Draft Error",
            color="red",
            variant="filled",
            withCloseButton=True
        )
        return error_msg, "Score: -", "Score: -", 50, "-", 50, "-"
    radiant_hero_ids = itemgetter(*radiant_team)(HERO_DICT)
    dire_hero_ids = itemgetter(*dire_team)(HERO_DICT)
    patch_id = PATCH_DICT[patch_name]
    radiant_draft_score = draft_service.compute_draft_strength(
        team_heroes=radiant_hero_ids,
        enemy_heroes=dire_hero_ids,
        patch=patch_id,
    )
    dire_draft_score = draft_service.compute_draft_strength(
        team_heroes=dire_hero_ids,
        enemy_heroes=radiant_hero_ids,
        patch=patch_id,
    )
    total_score = radiant_draft_score + dire_draft_score
    radiant_pct = (radiant_draft_score / total_score) * 100
    dire_pct = (dire_draft_score / total_score) * 100
    return (
        None,
        f"Score: {radiant_draft_score:.4f}", 
        f"Score: {dire_draft_score:.4f}",    
        radiant_pct, f"{radiant_pct:.4f}%", 
        dire_pct, f"{dire_pct:.4f}%"
    )
