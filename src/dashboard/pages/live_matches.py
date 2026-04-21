import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go
from zoneinfo import ZoneInfo

import time
import logging
logger = logging.getLogger(__name__)

from theme import PLOTLY_COLORSCALES, COLORS

from app_functions import *
from dashboard.filters import *
from live_match_monitor import LiveMatchMonitor

dash.register_page(__name__, path='/live-matches')

def layout(page=1, league=None, startDate=None, endDate=None, **kwargs):
    return dmc.Container(
        size='lg', 
        children=[ 
            dcc.Interval(id='live-update-timer', interval=30*1000, n_intervals=0),
            dmc.ScrollArea(
                h=600, 
                offsetScrollbars=True,
                children=[
                    dmc.Text('Test worked'),
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
    results = db.select_to_df(
        "SELECT * FROM live_matches WHERE status <> 'fetched_opendota' AND status <> 'failed_parse' ORDER BY last_updated DESC",
        table='live_matches'    
    )
    if results.empty:
        return dmc.Text("No live pro matches right now.", c="dimmed", ta="center", mt="xl")
    return [create_live_match_card(row) for _, row in results.iterrows()]

def create_live_match_card(row):
    radiant_lead = row['radiant_lead']
    is_radiant_lead = radiant_lead > 0
    lead_color = COLORS['radiant'] if is_radiant_lead else COLORS['dire']
    game_time = convert_duration_format(row['game_time'])
    league = row['league_name']
    is_unknown_League = (league == 'Unknown League')
    start_time = row['start_date_time'].astimezone(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")
    radiant_draft_score = round(row.get('radiant_draft_score'), 2)
    dire_draft_score = round(row.get('dire_draft_score'), 2)
    rad_rating = row.get('avg_radiant_rating', None)
    dire_rating = row.get('avg_dire_rating', None)
    if rad_rating:
        rad_rating = round(rad_rating, 2)
    else:
        rad_rating = '-'
    if dire_rating:
        dire_rating = round(dire_rating, 2)
    else:
        dire_rating = '-'
    return dmc.Paper(
        withBorder=True,
        shadow='sm',
        p='md',
        radius='md',
        style={"transition": "transform 0.2s ease"},
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
            ),
            
            dmc.Group(
                justify="center", 
                gap="xl",         
                children=[
                    dmc.Stack(
                        align="center", 
                        gap=0, 
                        w=150, 
                        children=[
                            dmc.Paper(
                                    shadow="xs",
                                    radius="md",
                                    p=5,
                                    withBorder=True,
                                    bg="white", # Forces a background so transparent logos are visible
                                    children=[
                                        dmc.Image(
                                            src=row['radiant_logo'] if row['radiant_logo'] else '/assets/no_image.svg', 
                                            fallbackSrc='/assets/no_image.svg',
                                            w=50, h=50, 
                                            fit="contain"
                                        )
                                    ]
                                ),
                            dmc.Text(row['radiant_name'], fw=700, size="sm", mt="sm", ta="center"), # ta="center" is key
                            dmc.Text(f"MMR: {rad_rating}", size="xs", c="dimmed"),
                            dmc.Text(f'Draft Score: {radiant_draft_score}', size="xs", c="dimmed")
                        ]
                    ),
                    
                    dmc.Text("VS", fw=900, size="lg", c="dimmed"),
                    
                    dmc.Stack(
                        align="center", 
                        gap=0, 
                        w=150, 
                        children=[
                            dmc.Paper(
                                shadow="xs",
                                radius="md",
                                p=5,
                                withBorder=True,
                                bg="white", # Forces a background so transparent logos are visible
                                children=[
                                    dmc.Image(
                                        src=row['dire_logo'] if row['dire_logo'] else '/assets/no_image.svg', 
                                        fallbackSrc='/assets/no_image.svg',
                                        w=50, h=50, 
                                        fit="contain"
                                    )
                                ]
                            ),
                            dmc.Text(row['dire_name'], fw=700, size="sm", mt="sm", ta="center"), 
                            dmc.Text(f"MMR: {dire_rating}", size="xs", c="dimmed"),
                            dmc.Text(f'Draft Score: {dire_draft_score}', size="xs", c="dimmed")
                        ]
                    )
                ]
            ),
            
            dmc.Divider(variant="dashed", my="sm"),
            
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Text(f"📅 {start_time}", size="xs", c="dimmed"),
                    dmc.Text(f"Current⏱️ {game_time}", size="xs", c="dimmed"),
                    dmc.Text(f"ID: {row['match_id']}", size="xs", c="dimmed")
                ]
            )
        ]
    )
