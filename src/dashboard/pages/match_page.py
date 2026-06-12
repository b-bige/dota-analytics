import dash
from dash import html
import dash_mantine_components as dmc
import logging
from src.dashboard.app_functions import *
from src.dashboard import db_manager

logger = logging.getLogger(__name__)

vs_logo = dmc.Avatar(
    "VS",
    radius="xl",
    size="lg",
    color="yellow", 
    variant="filled",
    style={
        "fontWeight": 900,
        "fontSize": "1.2rem",
        "boxShadow": "0 0 15px rgba(255, 193, 7, 0.3)",
        "border": "2px solid #2C2E33"
    }
)

dash.register_page(__name__, path_template='/match/<match_id>')

def layout(match_id=None, **kwargs):
    if not match_id:
        return dmc.Text("No Match ID provided", c="red", fw=500, p="md")
    return render_match_page(match_id)

def render_match_page(match_id):
    query = '''
        SELECT "didRadiantWin", "radiantTeamId", "direTeamId", "durationSeconds", radiant_score, dire_score
        FROM match_details WHERE id = :match_id
    '''
    res = db_manager.select(query, params={'match_id': match_id})[0]
    rad_win, rad_team_id, dire_team_id, duration, rad_score, dire_score = res 
    query = 'SELECT name, logo FROM team_details WHERE id = :team_id'
    rad = db_manager.select(query, params={'team_id': rad_team_id})
    dire = db_manager.select(query, params={'team_id': dire_team_id})
    
    logo_query = 'SELECT logo_url FROM team_logos WHERE team_id = :team_id'
    
    try:
        if rad:
            rad_name = rad[0][0]
            rad_logo = rad[0][1]
        else:
            rad_name = f'Radiant ID: {rad_team_id}'
            rad_logo = ''
    except Exception:
        rad_name = f'Radiant ID: {rad_team_id}'
        rad_logo = ''
        
    if not rad_logo:
        try:
            rad_logo = db_manager.select(logo_query, params={'team_id': rad_team_id})[0]
        except Exception:
            rad_logo = '/assets/no_image.svg'

    try:
        if dire:
            dire_name = dire[0][0]
            dire_logo = dire[0][1]
        else:
            dire_name = f'Dire ID: {dire_team_id}'
            dire_logo = ''
    except Exception:
        dire_name = f'Dire ID: {dire_team_id}'
        dire_logo = ''
        
    if not dire_logo:
        try:
            dire_logo = db_manager.select(logo_query, params={'team_id': dire_team_id})[0]
        except Exception:
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
                WHEN (mp."isRadiant" = true AND mp.position IN ('POSITION_3', 'POSITION_4')) OR 
                     (mp."isRadiant" = false AND mp.position IN ('POSITION_1', 'POSITION_5')) THEN 1
                WHEN mp.position = 'POSITION_2' THEN 2
                WHEN (mp."isRadiant" = true AND mp.position IN ('POSITION_1', 'POSITION_5')) OR 
                     (mp."isRadiant" = false AND mp.position IN ('POSITION_3', 'POSITION_4')) THEN 3
            END as lane_group
        FROM hero_details hd
        INNER JOIN match_players mp ON mp."heroId" = hd.id
        WHERE mp."match_id" = :match_id
        ORDER BY 
            mp."isRadiant" DESC,
            CASE 
                WHEN mp."isRadiant" = true THEN
                    CASE 
                        WHEN mp.position IN ('POSITION_3', 'POSITION_4') THEN 1
                        WHEN mp.position = 'POSITION_2' THEN 2
                        WHEN mp.position IN ('POSITION_1', 'POSITION_5') THEN 3
                    END
                ELSE
                    CASE 
                        WHEN mp.position IN ('POSITION_1', 'POSITION_5') THEN 1
                        WHEN mp.position = 'POSITION_2' THEN 2
                        WHEN mp.position IN ('POSITION_3', 'POSITION_4') THEN 3
                    END
            END ASC,
            mp.position ASC
    '''
    players_list = db_manager.select(query, params={'match_id': match_id})
    rad_total_networth = np.sum([p[4] for p in players_list[:5]])
    dire_total_networth = np.sum([p[4] for p in players_list[5:]])
    lead_value = rad_total_networth - dire_total_networth
    if lead_value > 0:
        lead_text = f"+{lead_value:,} Radiant Gold"
        lead_color = COLORS['radiant']
    elif lead_value < 0:
        lead_text = f"+{abs(lead_value):,} Dire Gold"
        lead_color = COLORS['dire']
    else:
        lead_text = "Even Gold"
        lead_color = "gray"
    return dmc.Container(size="xl", fluid=True, children=[
        dmc.Grid(gutter="md", children=[
            
            dmc.GridCol(span=12, children=[
                dmc.Paper(withBorder=True, p="md", radius="md", children=[
                    html.Div(style={"display": "flex", "alignItems": "center", "width": "100%"}, children=[

                        html.Div(style={"flex": "1 1 0", "display": "flex", "alignItems": "center", "justifyContent": "flex-end", "gap": "16px"}, children=[
                            dmc.Text(f"{rad_name or "Radiant"}", fw=700, size="xl"),
                            dmc.Image(src=rad_logo, w=70, style={"borderRadius": "4px"}),
                            dmc.Text(f"{rad_score or 0}", fw=800, size="3rem", c=COLORS['radiant']),
                        ]),

                        html.Div(style={"flex": "0 0 auto", "padding": "0 32px", "display": "flex", "flexDirection": "column", "alignItems": "center", "gap": "4px"}, children=[
                            vs_logo,
                            dmc.Text(format_game_time(duration or 0), fw=600, size="md", c="dimmed", style={"marginTop": "8px"}),
                            dmc.Badge(lead_text, color=lead_color, variant="light")
                        ]),

                        html.Div(style={"flex": "1 1 0", "display": "flex", "alignItems": "center", "justifyContent": "flex-start", "gap": "16px"}, children=[
                            dmc.Text(f"{dire_score or 0}", fw=800, size="3rem", c=COLORS['dire']),
                            dmc.Image(src=dire_logo, w=70, style={"borderRadius": "4px"}),
                            dmc.Text(f"{dire_name or "Dire"}", fw=700, size="xl"),
                        ]),
                    ])
                ])
            ]),
            
            dmc.GridCol(span=12, children=[
                dmc.Stack([
                    dmc.Text("Radiant Performance", fw=700, size="xl", c="green"),
                    create_match_table(players_list[:5], True)
                ], gap="xs")
            ]),

            dmc.GridCol(span=12, children=[
                dmc.Stack([
                    dmc.Text("Dire Performance", fw=700, size="xl", c="red"),
                    create_match_table(players_list[5:], False)
                ], gap="xs")
            ]),
        ])
    ])

def create_match_table(players_list, is_radiant: bool):
    header = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("Hero", style={'width': '25%'}),
            dmc.TableTh('K / D / A', style={'width': '15%', "textAlign": "right"}),
            dmc.TableTh("Networth", style={'width': '15%', "textAlign": "right"}),
            dmc.TableTh("GPM", style={'width': '15%', "textAlign": "right"}),
            dmc.TableTh("Hero Damage", style={'width': '15%', "textAlign": "right"}),
            dmc.TableTh("Tower Damage", style={'width': '15%', "textAlign": "right"}),
        ])
    )
    rows = [create_match_row(*player) for player in players_list] 
    
    border_color = '#40c057' if is_radiant else '#fa5252'
    return dmc.Table(
        children=[header, dmc.TableTbody(rows)],
        verticalSpacing='xs',
        highlightOnHover=True,
        withTableBorder=True,
        style={
            'tableLayout': 'fixed', 
            'width': '100%', 
            "borderTop": f"4px solid {border_color}"
        }
    )

def create_match_row(hero_name, hero_display_name, is_radiant, position, networth, gpm, hero_dmg, tower_dmg, steam_acc_id, kills, deaths, assists, lane_group):
    img_url = f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{hero_name}.png"
    
    fmt_kills = kills if kills is not None else '-'
    fmt_deaths = deaths if deaths is not None else '-'
    fmt_assists = assists if assists is not None else '-'
    kda = f'{fmt_kills} / {fmt_deaths} / {fmt_assists}'

    fmt_metric = lambda val: f"{val:,}" if val is not None else '-'

    return dmc.TableTr([
        dmc.TableTd(
            dmc.Group([
                dmc.Image(src=img_url, w=45, radius="xs", fallbackSrc='/assets/no_image.svg'),
                dmc.Text(hero_display_name, size="sm", fw=600, truncate="end")
            ], gap="sm")
        ),
        dmc.TableTd(kda, style={'textAlign': 'right', 'fontFamily': 'monospace'}),
        dmc.TableTd(fmt_metric(networth), style={"textAlign": "right", 'color': '#fcc419' if networth else None}),
        dmc.TableTd(fmt_metric(gpm), style={"textAlign": "right"}),
        dmc.TableTd(fmt_metric(hero_dmg), style={"textAlign": "right"}),
        dmc.TableTd(fmt_metric(tower_dmg), style={"textAlign": "right"}),
    ])