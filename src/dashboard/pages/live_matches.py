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
from live_match_monitor import LiveMatchMonitor

dash.register_page(__name__, path='/live-matches')

def layout(page=1, league=None, startDate=None, endDate=None, **kwargs):
    return dmc.Container(
        size='lg', 
        children=[ 
            dcc.Interval(id='live-update-timer', interval=30*1000, n_intervals=0),
            dmc.ScrollArea(
                h=600, # Fixed height helps with ScrollArea behavior
                offsetScrollbars=True,
                children=[
                    dmc.SimpleGrid(
                        id='live-match-container', 
                        cols=2,        # Force 2 items per row
                        spacing="md",  # Gap between cards,
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
    results = db.query_select('SELECT * FROM live_matches ORDER BY last_updated DESC')
    if not results:
        return dmc.Text("No live pro matches right now.", c="dimmed", ta="center", mt="xl")
    columns = [
        'match_id', 'league_id', 'league_name', 'start_date',
        'radiant_id', 'dire_id',
        'radiant_name', 'dire_name',
        'radiant_logo', 'dire_logo',
        'radiant_score', 'dire_score', 
        'game_time', 'radiant_lead',
        'last_updated', 'is_finished'
    ]
    matches = [dict(zip(columns, row)) for row in results]
    return [create_live_match_card(row) for row in matches]

def create_live_match_card(row):
    radiant_lead = row['radiant_lead']
    is_radiant_lead = radiant_lead > 0
    lead_color = COLORS['radiant'] if is_radiant_lead else COLORS['dire']
    game_time = convert_duration_format(row['game_time'])
    league = row['league_name']
    is_unknown_League = (league == 'Unknown League')
    return dmc.Paper(
        withBorder=True,
        shadow='sm',
        p='md',
        radius='md',
        # A subtle hover effect makes it feel like an interactive app
        style={"transition": "transform 0.2s ease"},
        # className="match-card-hover",
        children=[
            # 1. HEADER: League & Match Result
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
            
            # 2. BODY: The "VS" Matchup
            dmc.Group(
                justify="center", 
                gap="xl",         
                children=[
                    # Radiant Side - Fixed width ensures symmetry
                    dmc.Stack(
                        align="center", 
                        gap=0, 
                        w=150, # <--- Add this
                        children=[
                            dmc.Image(
                                src=row['radiant_logo'] if row['radiant_logo'] else '/assets/no_image.svg', 
                                w=50, h=50, fit="contain"
                            ),
                            dmc.Text(row['radiant_name'], fw=700, size="sm", mt="sm", ta="center"), # ta="center" is key
                        ]
                    ),
                    
                    # The "VS" Text
                    dmc.Text("VS", fw=900, size="lg", c="dimmed"),
                    
                    # Dire Side - Same fixed width
                    dmc.Stack(
                        align="center", 
                        gap=0, 
                        w=150, # <--- Add this
                        children=[
                            dmc.Image(
                                src=row['dire_logo'] if row['dire_logo'] else '/assets/no_image.svg', 
                                w=50, h=50, fit="contain"
                            ),
                            dmc.Text(row['dire_name'], fw=700, size="sm", mt="sm", ta="center"), # ta="center" is key
                        ]
                    )
                ]
            ),
            
            # Divider to separate stats
            dmc.Divider(variant="dashed", my="sm"),
            
            # 3. FOOTER: Match Metadata
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Text(f"📅 {row['start_date']}", size="xs", c="dimmed"),
                    dmc.Text(f"Current⏱️ {game_time}", size="xs", c="dimmed"),
                    dmc.Text(f"ID: {row['match_id']}", size="xs", c="dimmed")
                ]
            )
        ]
    )
