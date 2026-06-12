import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go
from zoneinfo import ZoneInfo
import numpy as np

import time
import logging
logger = logging.getLogger(__name__)

from src.dashboard.theme import PLOTLY_COLORSCALES, COLORS

from src.dashboard.app_functions import *
from src.dashboard.filters import *
from src.dashboard import db_manager

dash.register_page(__name__, path='/live-matches')

def layout(page=1, league=None, startDate=None, endDate=None, **kwargs):
    return dmc.Container(
        size='lg', 
        children=[ 
            dcc.Interval(id='live-update-timer', interval=15*1000, n_intervals=0),
            dmc.ScrollArea(
                h=600, 
                offsetScrollbars=True,
                children=[
                    dmc.SimpleGrid(
                        id='live-match-container', 
                        cols=2,        
                        spacing="md",  
                        mt=10,
                        children=[]
                    )
                ]
            ),
            dmc.Space(h='md')
        ]
    )

@callback(
        Output('live-match-container', 'children'),
        Input('live-update-timer', 'n_intervals')
)
def update_live_ui(n):
    results = db_manager.select_to_df( #TODO Change the active 
        "SELECT * FROM live_matches WHERE status = 'active' ORDER BY start_date_time DESC" 
    )
    if results.empty:
        return dmc.Text("No live pro matches right now.", c="dimmed", ta="center", mt="xl")
    return [create_live_match_card(row) for _, row in results.iterrows()]


def create_live_match_card(row):
    radiant_lead = row['radiant_lead']
    is_radiant_lead = radiant_lead > 0
    lead_color = COLORS['radiant'] if is_radiant_lead else COLORS['dire']
    game_time = format_game_time(row['game_time'])
    league = row['league_name']
    is_unknown_League = (league == 'Unknown League')
    start_time = row['start_date_time'].astimezone(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")
    
    radiant_draft_score = int(np.round(row.get('radiant_draft_score', 50)))
    dire_draft_score = int(np.round(row.get('dire_draft_score', 50)))
    
    rad_rating = np.round(row.get('avg_radiant_rating'), 2) if row.get('avg_radiant_rating') else '-'
    dire_rating = np.round(row.get('avg_dire_rating'), 2) if row.get('avg_dire_rating') else '-'
    
    rad_win_predicted = row.get('rad_win_predicted', None)
    
    if not rad_win_predicted:
        prediction_ui = dmc.Text(f'Updating model...', fw=700, c=COLORS['text_bright'])
    else:
        rad_prob = int(np.round(rad_win_predicted * 100))
        dire_prob = 100 - rad_prob
        
        prediction_ui = dmc.Stack(
            gap="xs",
            children=[
                dmc.Group(
                    justify="space-between",
                    children=[
                        dmc.Text(f"Radiant {rad_prob}%", fw=800, c=COLORS['radiant']),
                        dmc.Text("Win Probability", size="xs", c="dimmed", fw=600, tt="uppercase"),
                        dmc.Text(f"{dire_prob}% Dire", fw=800, c=COLORS['dire']),
                    ]
                ),
                html.Div(
                    style={
                        'display': 'flex', 
                        'height': '10px', 
                        'borderRadius': '5px', 
                        'overflow': 'hidden',
                        'backgroundColor': COLORS['dire'] 
                    },
                    children=[
                        html.Div(
                            style={
                                'width': f'{rad_prob}%', 
                                'backgroundColor': COLORS['radiant'],
                                'transition': 'width 0.5s ease-in-out'
                            }
                        ),
                        html.Div(
                            style={
                                'width': f'{dire_prob}%', 
                                'backgroundColor': COLORS['dire'],
                                'transition': 'width 0.5s ease-in-out'
                            }
                        )
                    ]
                )
            ]
        )

    return dcc.Link(
        href=f'/live-match/{row['match_id']}',
        refresh=False,
        style={'textDecoration': 'none', 'color': 'inherit', 'display': 'block'}, 
        children=dmc.Paper(
            withBorder=True,
            shadow='sm',
            p='md',
            radius='md',
            style={
                'display': 'flex',
                'flexDirection': 'column',
                "transition": "transform 0.2s ease"
            },
            className='match-card-hover',
            children=[
                html.Div(
                    style={'flex': 1},
                    children=[
                        dmc.Group(
                            justify="space-between",
                            mb="md",
                            children=[
                                dmc.Group(
                                    children=[
                                        dmc.Badge(league, variant='outline' if is_unknown_League else 'gradient'),
                                        dmc.Badge('Finished', variant='filled') if row['is_finished'] else None,
                                    ]
                                ),
                                dmc.Badge('Radiant Lead' if is_radiant_lead else 'Dire Lead', color=lead_color, variant='filled')
                            ]
                        )
                    ]
                ),
                dmc.Group(
                    justify="center", 
                    gap="xl",         
                    children=[
                        # Radiant Stack
                        dmc.Stack(
                            align="center", 
                            gap=0, 
                            w=150, 
                            children=[
                                dmc.Text('Radiant', fw=700, c=COLORS['radiant']),
                                dmc.Paper(
                                    shadow="xs", radius="md", p=5, withBorder=True, bg="white", 
                                    children=[
                                        dmc.Image(
                                            src=row['radiant_logo'] if row['radiant_logo'] else '/assets/no_image.svg', 
                                            fallbackSrc='/assets/no_image.svg',
                                            w=50, h=50, fit="contain"
                                        )
                                    ]
                                ),
                                dmc.Text(row['radiant_name'], fw=700, size="sm", mt="sm", ta="center", lineClamp=1),
                                dmc.Text(f"MMR: {rad_rating}", size="xs", c="dimmed"),
                                dmc.Text(f'Draft: {radiant_draft_score}%', size="sm", fw=600, c=COLORS['radiant']), # Updated!
                            ]
                        ),
                        
                        dmc.Text("VS", fw=900, size="lg", c="dimmed"),
                        
                        # Dire Stack
                        dmc.Stack(
                            align="center", 
                            gap=0, 
                            w=150, 
                            children=[
                                dmc.Text('Dire', fw=700, c=COLORS['dire']),
                                dmc.Paper(
                                    shadow="xs", radius="md", p=5, withBorder=True, bg="white",
                                    children=[
                                        dmc.Image(
                                            src=row['dire_logo'] if row['dire_logo'] else '/assets/no_image.svg', 
                                            fallbackSrc='/assets/no_image.svg',
                                            w=50, h=50, fit="contain"
                                        )
                                    ]
                                ),
                                dmc.Text(row['dire_name'], fw=700, size="sm", mt="sm", ta="center", lineClamp=1), 
                                dmc.Text(f"MMR: {dire_rating}", size="xs", c="dimmed"),
                                dmc.Text(f'Draft: {dire_draft_score}%', size="sm", fw=600, c=COLORS['dire']), # Updated!
                            ]
                        )
                    ]
                ),
                html.Div(
                    children=[
                        dmc.Divider(variant="dashed", my="sm"),
                
                        dmc.Group(
                            justify="space-between",
                            children=[
                                dmc.Text(f"📅 {start_time}", size="xs", c="dimmed"),
                                dmc.Text(f"⏱️ {game_time}", size="xs", c="dimmed"),
                                dmc.Text(f"ID: {row['match_id']}", size="xs", c="dimmed")
                            ]
                        ),
                        dmc.Divider(variant="dashed", my="sm"),
                        
                        html.Div(
                            children=[
                                prediction_ui
                            ]
                        )
                    ]
                )        
            ]
        )
    )