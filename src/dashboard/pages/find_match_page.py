import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
import dash_mantine_components as dmc

from math import floor
from urllib.parse import parse_qs

import os
import sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../"))
SRC_DIR = os.path.abspath(os.path.join(DASHBOARD_DIR, '../'))
sys.path.append(DASHBOARD_DIR)
sys.path.append(SRC_DIR)

from app_functions import *
from dashboard.filters import *

vs_logo = dmc.Avatar(
    "VS",
    radius="xl",
    size="lg",
    color=COLORS['primary'],
    variant="filled"
)

dash.register_page(__name__, path='/find-match')

# Dash Pages allows 'layout' to be a function to capture search params
def layout(page=1, league=None, startDate=None, endDate=None, **kwargs):
    return dmc.Container(
        children=[ 
            dmc.ScrollArea(
                h=600, # Fixed height helps with ScrollArea behavior
                offsetScrollbars=True,
                children=[
                    dmc.Stack(id='match-container', children=[])
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

@callback( 
        Output(component_id='match-container', component_property='children'),
        Output('match-pagination', 'total'),
        Output('match-pagination', 'value'),
        State('url', 'pathname'),
        State('url', 'search'),
        Input('match-pagination', 'value'),
        *[Input(component_id, 'value') for component_id in FILTER_IDS.values()],
        prevent_initial_call=True
)
def update_match_container_and_pages(pathname, search, page_number, *args): #TODO: Add pagination
    if pathname != '/find-match':
        return no_update
    triggered = ctx.triggered_id
    filters = {
        f.filter_name: ctx.inputs.get(f'{f.component_id}.value')
        for f in FILTERS
    }
    
    PAGE_SIZE = 20
    qb = QueryBuilder()
    Filter.handle_filters(qb, **filters)
    query, params = qb.build(select='COUNT(md.id)')
    total_records = db.query_select(query, params=params)[0][0]
    total_pages = -(-total_records // PAGE_SIZE)  # ceiling division

    # check if page should reset
    if triggered != 'match-pagination':
        url_params = parse_qs(search.lstrip('?'))
        url_filters = {
            f.filter_name: f.parse_from_url(url_params)
            for f in FILTERS
        }
        filter_matches_url = all(
            filters[f.filter_name] == url_filters[f.filter_name]
            for f in FILTERS
        )
        page_number = 1 if not filter_matches_url or page_number > total_pages else page_number

    offset = (int(page_number) - 1) * PAGE_SIZE
    qb.join('radiant', 'LEFT JOIN team_details radiant ON radiant.id = md."radiantTeamId"')
    qb.join('dire',    'LEFT JOIN team_details dire ON dire.id = md."direTeamId"')
    qb.join('ld',      'LEFT JOIN league_details ld ON md."leagueId" = ld.id')

    query, params = qb.build(
        select='''
            md.id, md."radiantTeamId", md."direTeamId",
            md."didRadiantWin", md."durationSeconds", md."startDateTimeHuman",
            radiant.name, dire.name, radiant.logo, dire.logo, ld."displayName"
        ''',
        order_by='ORDER BY md."startDateTimeHuman" ASC LIMIT %s OFFSET %s',
        extra_params=[PAGE_SIZE, offset]
    )

    columns = [
        'match_id', 'radiant_team_id', 'dire_team_id',
        'radiant_win', 'duration', 'start_date',
        'radiant_name', 'dire_name', 'radiant_logo', 'dire_logo', 'league_name'
    ]
    matches = [dict(zip(columns, row)) for row in db.query_select(query, params=params)]
    elements = [create_match_element(row) for row in matches]
    return elements, total_pages, page_number
    

def create_match_element(row: dict):
    result_color = COLORS['radiant'] if row['radiant_win'] else COLORS['dire']
    row['duration'] = convert_duration_format(row['duration'])
    return dcc.Link(
        dmc.Paper(
            withBorder=True,
            shadow='sm',
            p='md',
            mb='sm', # Margin bottom for spacing
            children=[
                dmc.Group([
                    dmc.Image(
                        src=row['radiant_logo'] if row['radiant_logo'] else '/assets/no_image.svg',
                        w=50
                    ),
                    dmc.Text(f'{row['radiant_name']} vs {row['dire_name']}'),
                    dmc.Image(
                        src=row['dire_logo'] if row['dire_logo'] else '/assets/no_image.svg',
                        w=50
                    ),
                    dmc.Badge('Radiant win', color=result_color, variant='filled') if row['radiant_win']
                    else dmc.Badge('Dire win', color=result_color, variant='filled'),
                    dmc.Badge(f'{row['league_name'] if row['league_name'] else 'League not found'}', variant='gradient')
                ], pos='apart'),
                dmc.Text(f'Duration: {row['duration']}', size='sm', c='dimmed'),
                dmc.Text(f'Start date: {row['start_date']}', size='sm', c='dimmed'),
                dmc.Text(f'ID: {row["match_id"]}', size='sm', c='dimmed')
            ]
        ),
        href=f'/match/{row['match_id']}',
        refresh=False,
        style={'textDecoration': 'none', 'color': 'inherit'}
    )
