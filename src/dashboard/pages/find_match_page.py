import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
import dash_mantine_components as dmc
from math import floor
from urllib.parse import parse_qs
from datetime import datetime
from zoneinfo import ZoneInfo
from src.dashboard import db_manager
from src.dashboard.app_functions import *
from src.dashboard.filters import *

vs_logo = dmc.Avatar(
    "VS",
    radius="xl",
    size="lg",
    color=COLORS['primary'],
    variant="filled"
)

dash.register_page(__name__, path='/find-match')

def layout(page=1, league=None, startDate=None, endDate=None, **kwargs):
    return dmc.Container(
        size='lg',
        children=[ 
            dcc.Loading(
                dmc.ScrollArea(
                    h=550,
                    offsetScrollbars=True,
                    children=[
                        dmc.SimpleGrid(
                            id='match-container', 
                            cols=2,        
                            spacing="md", 
                            mt=10,
                            children=[]
                        )
                    ]
                ),
                type='circle',
                color=COLORS['primary']
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
def update_match_container_and_pages(pathname, search, page_number, *args): 
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
    total_records = db_manager.select(query, params=params)[0][0]
    total_pages = -(-total_records // PAGE_SIZE)  

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
            radiant.name, dire.name, radiant.logo, dire.logo, ld."displayName", 
            md.avg_radiant_rating, md.avg_dire_rating, 
            md.radiant_draft_score, md.dire_draft_score
        ''',
        order_by='ORDER BY md."startDateTimeHuman" DESC LIMIT :page_size OFFSET :offset', #TODO: Make a separate clause for these in querybuilder
        extra_params={'page_size': PAGE_SIZE, 'offset': offset}
    )

    columns = [
        'match_id', 'radiant_team_id', 'dire_team_id',
        'radiant_win', 'duration', 'start_date',
        'radiant_name', 'dire_name', 'radiant_logo', 'dire_logo', 'league_name',
        'rad_rating', 'dire_rating', 'radiant_draft_score', 'dire_draft_score'
    ]
    matches = [dict(zip(columns, row)) for row in db_manager.select(query, params=params)]
    elements = [create_match_element(row) for row in matches]
    return elements, total_pages, page_number
    

def create_match_element(row: dict):
    result_color = COLORS['radiant'] if row['radiant_win'] else COLORS['dire']
    row['duration'] = convert_duration_format(row['duration'])
    start_date = row['start_date'].astimezone(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")
    league = row.get('league_name', None)
    rad_rating = row.get('rad_rating', None)
    dire_rating = row.get('dire_rating', None)
    radiant_draft_score = row.get('radiant_draft_score')
    dire_draft_score = row.get('dire_draft_score')
    if radiant_draft_score:
        radiant_draft_score = round(radiant_draft_score, 2)
    else:
        radiant_draft_score = 0.5
    if dire_draft_score: 
        dire_draft_score = round(dire_draft_score, 2) 
    else:
        dire_draft_score = 0.5
    if rad_rating:
        rad_rating = round(rad_rating, 2)
    else:
        rad_rating = '-'
    if dire_rating:
        dire_rating = round(dire_rating, 2)
    else:
        dire_rating = '-'
    return dcc.Link(
        href=f"/match/{row['match_id']}",
        refresh=False,
        style={'textDecoration': 'none', 'color': 'inherit', 'display': 'block'}, 
        children=[
            dmc.Paper(
                withBorder=True,
                shadow='sm',
                p='md',
                radius='md',
                style={"transition": "transform 0.2s ease"},
                className="match-card-hover",
                children=[
                    
                    dmc.Group(
                        justify="space-between",
                        mb="md",
                        children=[
                            dmc.Badge(league, variant='gradient') if league else dmc.Badge('Unknown league', variant='outline'),
                            dmc.Badge('Radiant Win' if row['radiant_win'] else 'Dire Win', color=result_color, variant='filled')
                        ]
                    ),
                    
                    dmc.Group(
                        justify="center", 
                        gap="xl",         
                        children=[
                            dmc.Stack(align="center", gap=0, children=[
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
                                dmc.Text(row['radiant_name'], fw=700, size="sm", mt="sm") if row['radiant_name'] else
                                dmc.Text(f'Radiant ID: {row['radiant_team_id']}'),
                                dmc.Text(f"MMR: {rad_rating}", size="xs", c="dimmed"),
                                dmc.Text(f'Draft Score: {radiant_draft_score}', size="xs", c="dimmed")
                            ]),
                            
                            dmc.Text("VS", fw=900, size="lg", c="dimmed"),
                            
                            dmc.Stack(align="center", gap=0, children=[
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
                                dmc.Text(row['dire_name'], fw=700, size="sm", mt="sm") if row['dire_name'] else
                                dmc.Text(f'Dire ID: {row['dire_team_id']}'),
                                dmc.Text(f"MMR: {dire_rating}", size="xs", c="dimmed"),
                                dmc.Text(f'Draft Score: {dire_draft_score}', size="xs", c="dimmed")
                            ])
                        ]
                    ),
                    
                    dmc.Divider(variant="dashed", my="sm"),
                    
                    dmc.Group(
                        justify="space-between",
                        children=[
                            dmc.Text(f"📅 {start_date}", size="xs", c="dimmed"),
                            dmc.Text(f"⏱️ {row['duration']}", size="xs", c="dimmed"),
                            dmc.Text(f"ID: {row['match_id']}", size="xs", c="dimmed")
                        ]
                    )
                ]
            )
        ]
    )
