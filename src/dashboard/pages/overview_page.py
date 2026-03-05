import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

from theme import PLOTLY_COLORSCALES, COLORS

from app_functions import *

dash.register_page(__name__, path='')

query = 'SELECT md.id FROM match_details md'
match_ids = [res[0] for res in db.query_select(query)]
query = '''
    SELECT AVG(CAST(mp."isVictory" AS INT)) AS winrate,
        COUNT(*) as picks,
        hd."displayName"
    FROM match_players mp
    JOIN hero_details hd 
    ON mp."heroId" = hd.id
    GROUP BY hd."displayName"
    HAVING COUNT(*) >= %s
    ORDER BY winrate DESC
    LIMIT 5
'''
min_picks = max(2, len(match_ids) // 10)
winrates = pd.DataFrame(
    db.query_select(query, params=(min_picks, )), 
    columns=['winrate', 'picks', 'hero']
).convert_dtypes().sort_values('winrate')
winrates['winrate'] = winrates['winrate'].astype('Float32')
winrates['winrate'] = winrates['winrate'].round(2)
top_heroes_overview_fig = go.Figure()
top_heroes_overview_fig.add_trace(
    go.Bar(
        x=winrates['winrate'],
        y=winrates['hero'],
        orientation='h',
        marker=dict(
            color=winrates['winrate'],        # use actual values for color mapping
            colorscale=PLOTLY_COLORSCALES['winrate'],
            showscale=False,                  # set True if you want the colorbar
        ),
        customdata=winrates['picks'],
        text=[f"{w:.0%}" for w in winrates['winrate']],
        textposition='outside'
    )
)
top_heroes_overview_fig = apply_fig_theme(top_heroes_overview_fig)
top_heroes_overview_fig.update_layout(
    title="Top 5 heroes",
    width=600,
    xaxis=dict(title_text = 'Hero winrate', tickformat=".0%", range=[0, max(winrates['winrate']) * 1.15], showgrid=False),  # 15% breathing room
    yaxis=dict(showgrid=False)
)

def layout(**kwargs):
    return [
        html.Div(
            style={
                "display": "flex",
                "width": "100%",
                "justifyContent": "space-evenly",
                'marginBottom': 20
            },
            children=[
                stat_card("Total Matches", id="total-matches"),
                stat_card("Win Rate (Radiant)", id="stat-radiant-win"),
                stat_card("Avg Game Length", id="stat-avg-duration"),
                # stat_card("Avg Kills", id="stat-total-kills"),
            ]
        ),
        html.Div(
            style={
                "display": "flex",
                "width": "100%",
                'alignItems': 'flex-start'
            },
            children=[
                dcc.Graph(
                    id='top-five-hero-winrate',
                    figure=top_heroes_overview_fig
                ),
                # html.Div(
                #     style={
                #         "display": "flex",
                #         "width": "100%",
                #         'justifyContent': 'space-evenly'
                #     },
                #     children=[
                #         dmc.Paper(
                #             id='most-picked',
                #             withBorder=True,
                #             p='lg',
                #             w=100,
                #             children=[
                #                 dmc.Text('Most picked hero'),
                #                 dmc.Image(id='most-picked-image', src='', radius='xs'),
                #                 dmc.Text(id='most-picked-name')
                #             ]
                #         ),
                #         dmc.Paper(
                #             withBorder=True,
                #             p='lg',
                #             w=100,
                #             children=[
                #                 dmc.Text('Most banned hero'),
                #                 dmc.Image(id='most-banned-image', src='', radius='xs'),
                #                 dmc.Text(id='most-banned-name')
                #             ]
                #         )
                #     ]
                # )
                
            ]
        )
    ]

@callback(
        Output('top-five-hero-winrate', 'figure'),
        # Output('most-picked-image', 'src'),
        # Output('most-picked-name', 'children'),
        # Output('most-banned-image', 'src'),
        # Output('most-banned-name', 'children'),
        Input('league-filter', 'value'),
        Input('date-filter', 'value')
)
def update_top_heroes(league, dates):
    ### Handling filtering
    clauses, params = handle_filters(league=league, dates=dates)
    query = 'SELECT md.id FROM match_details md' + clauses
    match_ids = get_match_ids(query, params)
    ### Top 5 heroes
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
                showscale=False,                  # set True if you want the colorbar
            ),
            customdata=winrates['picks'],
            text=[f"{w:.0%}" for w in winrates['winrate']],
            textposition='outside'
        )
    )
    fig = apply_fig_theme(fig)
    fig.update_layout(
        title="Top 5 heroes",
        width=600,
        xaxis=dict(title_text = 'Hero winrate', tickformat=".0%", range=[0, max(winrates['winrate']) * 1.15], showgrid=False),  # 15% breathing room
        yaxis=dict(showgrid=False)
    )
    return fig

    # ### Most picked and banned heroes
    # pick_filter = 'COUNT(*) FILTER (WHERE mpb."isPick" = TRUE) AS count,'
    # ban_filter = 'COUNT(*) FILTER (WHERE mpb."isPick" = FALSE) AS count,'

    # results = {}

    # for key, query_filter in [('picked', pick_filter), ('banned', ban_filter)]:
    #     query = f'''
    #         SELECT
    #             {query_filter}
    #             hd."displayName",
    #             hd."shortName"
    #         FROM match_pick_bans mpb
    #         JOIN hero_details hd
    #         ON hd.id = mpb."heroId"
    #         WHERE mpb."heroId" IS NOT NULL
    #             AND mpb.match_id = ANY(%s)
    #         GROUP BY hd."displayName", hd."shortName"
    #         ORDER BY count DESC
    #         LIMIT 1;
    #     '''
    #     row = db.query_select(query, params=(match_ids,))
    #     results[key] = row[0] if row else None  # (count, display_name, npc_name)
    # most_picked = results['picked']
    # most_banned = results['banned']
    # print(most_picked)
    # most_picked_img = f'https://cdn.dota2.com/apps/dota2/images/heroes/{most_picked[2]}_vert.jpg'
    # most_banned_img = f'https://cdn.dota2.com/apps/dota2/images/heroes/{most_banned[2]}_vert.jpg'
    # print(most_picked_img)
    # return fig, most_picked_img, most_picked[1], most_banned_img, most_banned[1]




@callback(
        Output('total-matches', 'children'),
        Output('stat-radiant-win', 'children'),
        Output('stat-avg-duration', 'children'),
        Input("league-filter", "value"),
        Input("date-filter", "value")
)
def update_overview_stats(league, dates):
    clauses, params = handle_filters(league=league, dates=dates)
    rw_query = '''
        SELECT AVG(CAST("didRadiantWin" AS INT)) 
        FROM match_details md 
    ''' + clauses
    agl_query = '''
        SELECT AVG("durationSeconds") 
        FROM match_details md 
    ''' + clauses
    radiant_win = str(round(db.query_select(rw_query, params=params)[0][0], 2)) + '%'
    avg_game_length = convert_duration_format(db.query_select(agl_query, params=params)[0][0])
    found_matches = get_total_matches(clauses, params=params)
    return found_matches, radiant_win, avg_game_length

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