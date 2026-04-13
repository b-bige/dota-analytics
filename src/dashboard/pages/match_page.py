import dash
from dash import html
import dash_mantine_components as dmc
from app_functions import *
import logging
logger = logging.getLogger(__name__)

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

dash.register_page(__name__, path_template='/match/<match_id>')

def layout(match_id=None, **kwargs):
    if not match_id:
        return html.Div("No Match ID provided")
    return render_match_page(match_id)

def render_match_page(match_id):
    query = 'SELECT "didRadiantWin", "radiantTeamId", "direTeamId" FROM match_details WHERE id = %s'
    rad_win, rad_team_id, dire_team_id = db.select(query, params=(match_id, ))[0]
    query = 'SELECT name, logo FROM team_details WHERE id = %s'
    rad = db.select(query, params=(rad_team_id, ))
    dire = db.select(query, params=(dire_team_id, ))
    logo_query = 'SELECT logo_url FROM team_logos WHERE team_id = %s'
    try:
        if rad:
            rad_name = rad[0]
            rad_logo = rad[1]
        else:
            rad_name = f'Radiant ID: {rad_team_id}'
            rad_logo = ''
    except:
        rad_name = f'Radiant ID: {rad_team_id}'
        rad_logo = ''
    if not rad_logo:
        try:
            rad_logo = db.select(logo_query, params=(rad_team_id, ))[0]
        except:
            rad_logo = '/assets/no_image.svg'
    try:
        if dire:
            dire_name = dire[0]
            dire_logo = dire[1]
        else:
            dire_name = f'Dire ID: {dire_team_id}'
            dire_logo = ''
    except:
        dire_name = f'Dire ID: {dire_team_id}'
        dire_logo = ''
    if not dire_logo:
        try:
            dire_logo = db.select(logo_query, params=(dire_team_id, ))[0]
        except:
            dire_logo = '/assets/no_image.svg'
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
            mp.kills, 
            mp.deaths, 
            mp.assists,
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
    players_list = db.select(query, params=(match_id, ))
    result_color = COLORS['radiant'] if rad_win else COLORS['dire']
    return dmc.Container(size="xl", fluid=True, children=[
        dmc.Grid(gutter="md", children=[
            dmc.GridCol(span=12, children=[
                dmc.Paper(withBorder=True, p="md", children=[
                    html.Div(style={"display": "flex", "alignItems": "center", "width": "100%"}, children=[

                        html.Div(style={"flex": "1 1 0", "display": "flex", "alignItems": "center", "justifyContent": "flex-end", "gap": "12px"}, children=[
                            dmc.Badge('Radiant win', color=result_color, variant='filled') if rad_win else None,
                            dmc.Image(src=rad_logo if rad_logo else '/assets/no_image.svg', w=100),
                            dmc.Text(f'{rad_name}'),
                        ]),

                        html.Div(style={"flex": "0 0 auto", "padding": "0 24px"}, children=[
                            vs_logo
                        ]),

                        html.Div(style={"flex": "1 1 0", "display": "flex", "alignItems": "center", "justifyContent": "flex-start", "gap": "12px"}, children=[
                            dmc.Text(f'{dire_name}'),
                            dmc.Image(src=dire_logo if dire_logo else '/assets/no_image.svg', w=100),
                            dmc.Badge('Dire win', color=result_color, variant='filled') if not rad_win else None,
                        ]),
                    ])
                ])
            ]),
            
            dmc.GridCol(span=12, children=[
                dmc.Stack([
                    dmc.Text("Radiant", fw=700, c="green"),

                    create_match_table(players_list[:5], True)
                ])
            ]),

            dmc.GridCol(span=12, children=[
                dmc.Stack([
                    dmc.Text("Dire", fw=700, c="red"),
                    create_match_table(players_list[5:], False)
                ])
            ]),
        ])
    ])

def create_match_table(players_list, is_radiant:bool):
    header = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("Hero", style={'width': '30%'}),
            dmc.TableTh('K / D / A', style={'width': '15%', "textAlign": "right"}),
            dmc.TableTh("Networth", style={'width': '15%', "textAlign": "right"}),
            dmc.TableTh("GPM", style={'width': '15%', "textAlign": "right"}),
            dmc.TableTh("Hero Damage", style={'width': '15%', "textAlign": "right"}),
            dmc.TableTh("Tower Damage", style={'width': '15%', "textAlign": "right"}),
        ])
    )
    rows = []
    for player in players_list:
        rows.append(create_match_row(*player)) 
    return dmc.Table(
        children=[header, dmc.TableTbody(rows)],
        verticalSpacing='xs',
        highlightOnHover=True,
        withTableBorder=True,
        style={'tableLayout': 'fixed', 'width': '100%', "borderTop": f"4px solid {'#40c057' if is_radiant else '#fa5252'}"}
    )

def create_match_row(hero_name, hero_display_name, is_radiant, position, networth, gpm, hero_dmg, tower_dmg, steam_acc_id, kills, deaths, assists, lane_group):
    img_url = f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{hero_name}.png"
    if not kills:
        kills = '-'
    if not deaths:
        deaths = '-'
    if not assists:
        assists = '-'
    if networth:
        networth_td = dmc.TableTd(f"{networth:,}", style={"textAlign": "right"})
    else:
        networth_td = dmc.TableTd('-', style={"textAlign": "right"})
    kda = f'{str(kills)} / {str(deaths)} / {str(assists)}'

    return dmc.TableTr([
        dmc.TableTd(
            dmc.Group([
                dmc.Image(src=img_url, w=40, radius="xs"),
                dmc.Text(hero_display_name, size="sm", fw=600, truncate=True)
            ], gap="sm")
        ),
        dmc.TableTd(kda, style={'textAlign': 'right'}),
        networth_td,
        dmc.TableTd(f'{gpm:,}', style={"textAlign": "right"}),
        dmc.TableTd(f"{hero_dmg:,}", style={"textAlign": "right"}),
        dmc.TableTd(f"{tower_dmg:,}", style={"textAlign": "right"}),
    ])