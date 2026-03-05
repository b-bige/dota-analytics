import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

from app_functions import *

dash.register_page(__name__, path='')

def layout(**kwargs):
    return [
        html.Div(
            style={
                "display": "flex",
                "width": "100%",
                "justifyContent": "space-evenly"
            },
            children=[
                stat_card("Total Matches", id="total-matches"),
                stat_card("Win Rate (Radiant)", id="stat-radiant-win"),
                stat_card("Avg Game Length", id="stat-avg-duration"),
                stat_card("Avg Kills", id="stat-total-kills"),
            ]
        ),
        dcc.Graph(
            #TODO next: graaphs
        )
    ]

@callback(
        Output('total-matches', 'children'),
        Output('stat-radiant-win', 'children'),
        Output('stat-avg-duration', 'children'),
        Output('stat-total-kills', 'children'),
        Input("league-filter", "value"),
        Input("date-filter", "value")
)
def update_overview_stats(league, dates):
    base_where = 'WHERE 1=1'
    join = ''
    params = []
    if league:
        base_where += ' AND ld."displayName" = %s'
        join += ' JOIN league_details ld ON md."leagueId" = ld.id '
        params.append(league)
    if dates[0]:
        base_where, params = handle_date_filter(dates, base_where, params)
    rw_query = '''
        SELECT AVG(CAST("didRadiantWin" AS INT)) 
        FROM match_details md 
    ''' + join + base_where
    agl_query = '''
        SELECT AVG("durationSeconds") 
        FROM match_details md 
    ''' + join + base_where
    radiant_win = str(round(db.query_select(rw_query, params=params)[0][0], 2)) + '%'
    avg_game_length = convert_duration_format(db.query_select(agl_query, params=params)[0][0])
    modifiers = join + base_where
    found_matches = get_total_matches(modifiers, params=params)
    return found_matches, radiant_win, avg_game_length, None

def stat_card(label, id):
    return dmc.Paper(
        withBorder=True,
        p='lg',
        w=200,
        children=[
            dmc.Text(label, size='xs', c='dimmed', fw=700, tt="uppercase"),
            dmc.Title("0", id=id, order=2)
        ]
    )