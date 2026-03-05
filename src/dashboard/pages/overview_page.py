import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

from theme import PLOTLY_COLORSCALES, COLORS

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
        html.Div(
            style={
                "display": "flex",
                "width": "100%"
            },
            children=[
                dcc.Graph(
                    id='top-five-hero-winrate'
                )
            ]
        )
    ]

@callback(
        Output('top-five-hero-winrate', 'figure'),
        Input('league-filter', 'value'),
        Input('date-filter', 'value')
)
def update_top_heroes(league, dates):
    base_where = ' WHERE 1=1'
    join = ''
    params = []
    if league:
        base_where += ' AND ld."displayName" = %s'
        join += ' JOIN league_details ld ON md."leagueId" = ld.id '
        params.append(league)
    if dates[0]:
        base_where, params = handle_date_filter(dates, base_where, params)

    query = 'SELECT md.id FROM match_details md' + join + base_where
    match_ids = get_match_ids(query, params)
    query = '''
        SELECT AVG(CAST(mp."isVictory" AS INT)) AS winrate,
            COUNT(*) as picks,
            hd."displayName"
        FROM match_players mp
        JOIN hero_details hd 
        ON mp."heroId" = hd.id
        WHERE match_id = ANY(%s)
        GROUP BY hd."displayName"
        HAVING COUNT(*) >= %s
        ORDER BY winrate DESC
        LIMIT 5
    '''
    min_picks = max(2, len(match_ids) // 10)
    winrates = pd.DataFrame(
        db.query_select(query, params=(match_ids, min_picks)), 
        columns=['winrate', 'picks', 'hero']
    ).convert_dtypes().sort_values('winrate')
    winrates['winrate'] = winrates['winrate'].astype('Float32')
    winrates['winrate'] = winrates['winrate'].round(2)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=winrates['winrate'],
            y=winrates['hero'],
            orientation='h',
            marker=dict(
                color=winrates['winrate'],        # use actual values for color mapping
                colorscale=PLOTLY_COLORSCALES['winrate'],
                showscale=True,                  # set True if you want the colorbar
            ),
            customdata=winrates['picks'],
            text=[f"{w:.0%}" for w in winrates['winrate']],
            textposition='outside'
        )
    )
    fig = apply_fig_theme(fig)

    return fig

    


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