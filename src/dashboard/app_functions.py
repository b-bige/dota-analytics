import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from math import floor, ceil

from urllib.parse import urlencode, parse_qs

import os
import sys
sys.path.append(os.path.abspath('./src/dashboard'))
sys.path.append(os.path.abspath('./src'))

from db_functions import DotaDB

from dash import Dash, html, dcc, Input, Output, State, callback, ctx, no_update
import dash_mantine_components as dmc

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

##### Initial setup

def get_total_matches():
    return db.query_select('SELECT COUNT(*) FROM match_details;')[0][0]

def get_leagues():
    leagues = [result[0] for result in db.query_select(
        '''
            SELECT DISTINCT ld."displayName" dn
            FROM match_details md
                INNER JOIN league_details ld ON md."leagueId" = ld.id ORDER BY ld."displayName" ASC;
        '''
    )]
    return leagues

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

def get_date_boundary(boundary, league): 
    if league:
        query = f'''
            SELECT {boundary}(md."startDateTime") 
            FROM match_details md
            INNER JOIN league_details ld
            ON md."leagueId" = ld.id
            WHERE ld."displayName" = %s;
        '''
        return datetime.fromtimestamp(db.query_select(query, params=(league, ))[0][0])
    else:
        return datetime.fromtimestamp(db.query_select(f'SELECT {boundary}("startDateTime") FROM match_details;')[0][0])
    
##### Navigation 

@callback(
    Output(component_id='page-content', component_property='children'),
    Output('shell-navbar', 'children'),
    Output('shell-header', 'children'),
    Output('main-shell', 'navbar'),
    Input(component_id='url', component_property='pathname'),
    Input('url', 'search')
)
def display_page(pathname:str, search:str):
    if pathname == '/' or pathname is None:
        params = parse_qs(search.lstrip('?'))
        saved_league = params.get('league', [None])[0]
        saved_start = params.get('startDate', [None])[0]
        saved_end = params.get('endDate', [None])[0]
        navbar_content = dmc.ScrollArea(
            offsetScrollbars=True,
            children=[
                dmc.Select(
                    id='league-filter',
                    label='League',
                    placeholder='Select League',
                    data=get_leagues(),
                    value=saved_league,
                    searchable=True
                ),
                dmc.DatePicker(
                    id='date-filter',
                    type='range',
                    minDate=set_min_date(),
                    maxDate=set_max_date(),
                    value=[saved_start, saved_end]
                )
            ]
        )
        header_content = dmc.Group(
            children=[
                dmc.Title('Dota 2 Analytics'),
                dmc.Badge(f"{get_total_matches()} matches found", variant='gradient', size='xl',)
            ], justify='center'
        )
        navbar_config = {
            'width': 300, 
            'breakpoint': 'sm', 
            'collapsed': {'mobile': True, 'desktop': False}
        }
        return render_home_page(), navbar_content, header_content, navbar_config
    elif pathname.startswith('/match/'):
        match_id = pathname[7:] ## Strip the /match/
        header_content = dmc.Group(
            children=[
                dmc.Title(f'Match {match_id}') #TODO Add team names
            ], justify='center'
        ),
        navbar_config = {
            'width': 0, 
            'breakpoint': 'sm', 
            'collapsed': {'mobile': True, 'desktop': True}
        }
        return render_match_page(match_id), None, header_content, navbar_config
    
##### Rendering

def render_home_page():
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
    
def render_match_page(match_id):
    query = 'SELECT "radiantTeamId", "direTeamId" FROM match_details WHERE id = %s'
    rad_team_id, dire_team_id = db.query_select(query, params=(match_id, ))[0]
    query = '''
        SELECT 
            hd."shortName", 
            hd."displayName", 
            mp."isRadiant", 
            mp.position,
            mp.networth,
            mp."goldPerMinute",
            mp."heroDamage",
            mp."towerDamage",
            mp."steamAccountId",
            CASE 
                -- TOP LANE: Radiant Offlane (3,4) or Dire Safelane (1,5)
                WHEN (mp."isRadiant" = true AND mp.position IN ('POSITION_3', 'POSITION_4')) OR 
                    (mp."isRadiant" = false AND mp.position IN ('POSITION_1', 'POSITION_5')) THEN 1
                -- MID LANE: Position 2
                WHEN mp.position = 'POSITION_2' THEN 2
                -- BOT LANE: Radiant Safelane (1,5) or Dire Offlane (3,4)
                WHEN (mp."isRadiant" = true AND mp.position IN ('POSITION_1', 'POSITION_5')) OR 
                    (mp."isRadiant" = false AND mp.position IN ('POSITION_3', 'POSITION_4')) THEN 3
            END as lane_group
        FROM hero_details hd
        INNER JOIN match_players mp
        ON mp."heroId" = hd.id
        WHERE mp."match_id" = %s
        ORDER BY 
            mp."isRadiant" DESC, -- Radiant players grouped first
            CASE 
                -- Sorting Radiant: Top -> Mid -> Bot
                WHEN mp."isRadiant" = true THEN
                    CASE 
                        WHEN mp.position IN ('POSITION_3', 'POSITION_4') THEN 1
                        WHEN mp.position = 'POSITION_2' THEN 2
                        WHEN mp.position IN ('POSITION_1', 'POSITION_5') THEN 3
                    END
                -- Sorting Dire: Top -> Mid -> Bot
                ELSE
                    CASE 
                        WHEN mp.position IN ('POSITION_1', 'POSITION_5') THEN 1
                        WHEN mp.position = 'POSITION_2' THEN 2
                        WHEN mp.position IN ('POSITION_3', 'POSITION_4') THEN 3
                    END
            END ASC,
            mp.position ASC
    '''
    players_list = db.query_select(query, params=(match_id, ))

    return dmc.Container(size="xl", fluid=True, children=[
        dmc.Grid(gutter="md", children=[
            
            # --- ROW 1: HEADER STATS (Full Width) ---
            dmc.GridCol(span=12, children=[
                dmc.Paper(withBorder=True, p="md", children=[
                    dmc.Group([
                        dmc.Text(str(rad_team_id)), #TODO add names
                        vs_logo,            
                        dmc.Text(str(dire_team_id)) 
                    ], justify="center", gap="xl")
                ])
            ]),

            # --- ROW 2: THE MAIN BATTLEFIELD ---
            
            # 1. Radiant Heroes (3 columns)
            dmc.GridCol(span=12, children=[
                dmc.Stack([
                    dmc.Text("Radiant", fw=700, c="green"),
                    # Create 5 hero placeholders
                    create_match_table(players_list[:5], True)
                ])
            ]),

            # 3. Dire Heroes (3 columns)
            dmc.GridCol(span=12, children=[
                dmc.Stack([
                    dmc.Text("Dire", fw=700, c="red"),
                    # Create 5 hero placeholders
                    create_match_table(players_list[5:], False)
                ])
            ]),

            dmc.GridCol(span=8, children=[
                dmc.Paper(withBorder=True, p="sm", h="100%", children=[
                    dmc.Text("Net Worth Advantage", size="xs", mb="sm"),
                    dmc.Skeleton(height=300, width="100%"), # The Graph placeholder
                    dmc.Group([
                        dmc.Skeleton(height=40, width=100),
                        dmc.Skeleton(height=40, width=100),
                    ], justify="center", mt="md")
                ])
            ]),

            # --- ROW 3: REPLAY / LOGS (Full Width) ---
            dmc.GridCol(span=12, children=[
                dmc.Paper(withBorder=True, p="md", children=[
                    dmc.Skeleton(height=20, width="30%", mb="md"), # "Match Timeline" title
                    dmc.Skeleton(height=100, width="100%"),
                ])
            ])
        ])
    ])

def create_match_table(players_list, is_radiant:bool):
    header = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("Hero"),
            dmc.TableTh("Networth", style={"textAlign": "right"}),
            dmc.TableTh("GPM", style={"textAlign": "right"}),
            dmc.TableTh("Hero Damage", style={"textAlign": "right"}),
            dmc.TableTh("Tower Damage", style={"textAlign": "right"}),
        ])
    )
    rows = []
    for player in players_list:
        rows.append(create_match_row(*player[:9])) #TODO: remove is_radiant, position from params, add steam acc id somehow
    return dmc.Table(
        children=[header, dmc.TableTbody(rows)],
        verticalSpacing='xs',
        highlightOnHover=True,
        withTableBorder=True,
        style={"borderTop": f"4px solid {'#40c057' if is_radiant else '#fa5252'}"}
    )

def create_match_row(hero_name, hero_display_name, is_radiant, position, networth, gpm, hero_dmg, tower_dmg, steam_acc_id):
    img_url = f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{hero_name}.png"

    return dmc.TableTr([
        # Hero Cell: Image + Name
        dmc.TableTd(
            dmc.Group([
                dmc.Image(src=img_url, w=40, radius="xs"),
                dmc.Text(hero_display_name, size="sm", fw=600)
            ], gap="sm")
        ),
        # Stats Cells
        dmc.TableTd(f"{networth:,}", style={"textAlign": "right"}),
        dmc.TableTd(gpm, style={"textAlign": "right"}),
        dmc.TableTd(f"{hero_dmg:,}", style={"textAlign": "right"}),
        dmc.TableTd(f"{tower_dmg:,}", style={"textAlign": "right"}),
    ])

##### Filter saving

@callback(
    Output("url", "search"),
    Input("league-filter", "value"),
    Input("date-filter", "value"),
    State("url", "pathname"),
    prevent_initial_call=True
)
def update_url_from_filters(league, dates, pathname):
    if pathname != "/":
        return no_update
    params = {}
    if league: params["league"] = league
    if dates:
        if dates[0]: params["startDate"] = dates[0]
        if dates[1]: params["endDate"] = dates[1]
    return f"?{urlencode(params)}" if params else ""

##### Filtering

#TODO: split this and reduce the apply button
@callback( 
        Output(component_id='match-container', component_property='children'),
        Input(component_id='league-filter', component_property='value'),
        Input(component_id='date-filter', component_property='value'),
        prevent_initial_call=True
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