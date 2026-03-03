import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_mantine_components as dmc

from math import floor
from urllib.parse import urlencode

import os
import sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../"))
SRC_DIR = os.path.abspath(os.path.join(DASHBOARD_DIR, '../'))
sys.path.append(DASHBOARD_DIR)
sys.path.append(SRC_DIR)

from app_functions import *

db = DotaDB(schema='public')
vs_logo = dmc.Avatar(
    "VS",
    radius="xl",
    size="lg",
    color="yellow", # Dota gold
    variant="filled",
    style={
        "fontWeight": 900,
        "fontSize": "1.2rem",
        "boxShadow": "0 0 15px rgba(255, 193, 7, 0.3)", # Subtle glow
        "border": "2px solid #2C2E33"
    }
)

dash.register_page(__name__, path='/find-match')

# Dash Pages allows 'layout' to be a function to capture search params
def layout(league=None, startDate=None, endDate=None, **kwargs):
    return dmc.Container(
        children=[
            dmc.ScrollArea(
                offsetScrollbars=True,
                children=[
                    dmc.Stack(
                        id='match-container',
                        children=[]
                    ) #TODO: loading overlay
                ]
            )
        ]
    )

@callback(
        Output(component_id='date-filter', component_property='minDate'),
        Input(component_id='league-filter', component_property='value')
)
def set_min_date(league=None):
    return get_date_boundary('MIN', league)

@callback(
        Output(component_id='date-filter', component_property='maxDate'),
        Input(component_id='league-filter', component_property='value')
)
def set_max_date(league=None):
    return get_date_boundary('MAX', league)

@callback( 
        Output(component_id='match-container', component_property='children'),
        Input(component_id='league-filter', component_property='value'),
        Input(component_id='date-filter', component_property='value')
)
def update_match_container(league, dates): #TODO: Add pagination
    query = '''
        SELECT 
            md.id, 
            md."radiantTeamId",
            md."direTeamId",
            md."didRadiantWin",
            md."durationSeconds",
            md."startDateTime"
        FROM match_details md
        INNER JOIN league_details ld
        ON md."leagueId" = ld.id
        WHERE 1=1
    '''
    params = []
    if league:
        query += ' AND ld."displayName" = %s'
        params.append(league)
    if dates[0]:
        query += ' AND md."startDateTime" BETWEEN %s AND %s'
        start_date = datetime.fromisoformat(dates[0])
        if dates[0] and dates[1]:
            dates[1] = (datetime.fromisoformat(dates[1]) + timedelta(days=1)).timestamp()
        else:
            dates[1] = (start_date + timedelta(days=1)).timestamp()
        dates[0] = start_date.timestamp()
        params.extend(dates)
    columns=[
        'match_id', 
        'radiant_team_id',
        'dire_team_id',
        'radiant_win', 
        'duration',
        'start_date'
    ]
    matches = [dict(zip(columns, md)) for md in db.query_select(
        query=query,
        params=params
    )]          

    elements = [create_match_element(row) for row in matches]
    return elements

def create_match_element(row: dict):
    result_color = 'green' if row['radiant_win'] else 'red'
    minutes = str(floor(row['duration'] / 60))
    seconds = str(row['duration'] % 60)
    if len(seconds) == 1: #TODO: collapse into one 
        seconds += '0'
    row['duration'] = minutes + ':' + seconds
    row['start_date'] = datetime.fromtimestamp(row['start_date'])
    return dcc.Link(
        dmc.Paper(
            withBorder=True,
            shadow='sm',
            p='md',
            mb='sm', # Margin bottom for spacing
            children=[
                dmc.Group([
                    dmc.Badge(f'ID: {row["match_id"]}', variant='outline'),
                    dmc.Text(f'{row["radiant_team_id"]} vs {row["dire_team_id"]}'),
                    dmc.Badge('Radiant win', color=result_color, variant='filled') if row['radiant_win'] 
                    else dmc.Badge('Dire win', color=result_color, variant='filled')
                ], pos='apart'),
                dmc.Text(f'Duration: {row['duration']}', size='sm', c='dimmed'),
                dmc.Text(f'Start date: {row['start_date']}', size='sm', c='dimmed')
            ]
        ),
        href=f'/match/{row['match_id']}',
        refresh=False,
        style={"textDecoration": "none"}
    )

@callback(
    Output("url", "search"),
    Input("league-filter", "value"),
    Input("date-filter", "value"),
    prevent_initial_call=True
)
def update_url_from_filters(league, dates):
    params = {}
    if league: params["league"] = league
    if dates:
        if dates[0]: params["startDate"] = dates[0]
        if dates[1]: params["endDate"] = dates[1]
    return f"?{urlencode(params)}" if params else ""
