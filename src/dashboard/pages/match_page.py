import dash
from dash import html
import dash_mantine_components as dmc
from app_functions import *

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

# The <match_id> syntax tells Dash to pass that part of the URL as a variable
dash.register_page(__name__, path_template='/match/<match_id>')

def layout(match_id=None, **kwargs):
    if not match_id:
        return html.Div("No Match ID provided")
    return render_match_page(match_id)

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
                        dmc.Text(f'Radiant ({str(rad_team_id)})'), #TODO add names
                        vs_logo,            
                        dmc.Text(f'Dire ({str(dire_team_id)})')
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

            # dmc.GridCol(span=8, children=[
            #     dmc.Paper(withBorder=True, p="sm", h="100%", children=[
            #         dmc.Text("Net Worth Advantage", size="xs", mb="sm"),
            #         dmc.Skeleton(height=300, width="100%"), # The Graph placeholder
            #         dmc.Group([
            #             dmc.Skeleton(height=40, width=100),
            #             dmc.Skeleton(height=40, width=100),
            #         ], justify="center", mt="md")
            #     ])
            # ]),

            # # --- ROW 3: REPLAY / LOGS (Full Width) ---
            # dmc.GridCol(span=12, children=[
            #     dmc.Paper(withBorder=True, p="md", children=[
            #         dmc.Skeleton(height=20, width="30%", mb="md"), # "Match Timeline" title
            #         dmc.Skeleton(height=100, width="100%"),
            #     ])
            # ])
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