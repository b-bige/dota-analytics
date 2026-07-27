import dash
from dash import html, dcc, Input, Output, State, callback
import dash_mantine_components as dmc
import logging
import pandas as pd
from src.dashboard.app_functions import *
from src.dashboard import db_manager
from src.analytics import BettingHelper
from src.core.config import settings

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

dash.register_page(__name__, path_template='/live-match/<match_id>')

def layout(match_id=None, **kwargs):
    if not match_id:
        return dmc.Container(dmc.Alert("No Match ID provided", color="red"), size="xl")
    user_token = kwargs.get('secret')
    is_dev = (user_token == settings.dev_token)
    return render_live_match_page(match_id, is_dev)

def render_live_match_page(match_id, is_dev: bool):
    query = 'SELECT * FROM live_matches WHERE match_id = :match_id'
    df = db_manager.select_to_df(query, params={'match_id': match_id})
    
    if df.empty:
        return dmc.Container(dmc.Alert(f"Live match {match_id} not found.", color="red"), size="xl")
    
    match = df.iloc[0]
    
    rad_prob = float(match.get('rad_win_predicted', 0.5))
    dire_prob = 1.0 - rad_prob
    
    rad_logo = match.get('radiant_logo') or '/assets/radiant_icon.webp'
    dire_logo = match.get('dire_logo') or '/assets/dire_icon.webp'
    
    lead_value = match.get('radiant_lead', 0)
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
        dcc.Store(id='live-match-meta', data={'match_id': match_id}),
        dcc.Store(id='live-match-probabilities', data={'rad_prob': rad_prob, 'dire_prob': dire_prob}),
        
        dmc.Grid(gutter="md", children=[
            
            dmc.GridCol(span=12, children=[
                dmc.Paper(withBorder=True, p="md", radius="md", children=[
                    html.Div(style={"display": "flex", "alignItems": "center", "width": "100%"}, children=[

                        html.Div(style={"flex": "1 1 0", "display": "flex", "alignItems": "center", "justifyContent": "flex-end", "gap": "16px"}, children=[
                            dmc.Text(f"{match.get('radiant_name', 'Radiant')}", fw=700, size="xl"),
                            dmc.Image(src=rad_logo, w=70, style={"borderRadius": "4px"}),
                            dmc.Text(f"{match.get('radiant_score', 0)}", fw=800, size="3rem", c=COLORS['radiant']),
                        ]),

                        html.Div(style={"flex": "0 0 auto", "padding": "0 32px", "display": "flex", "flexDirection": "column", "alignItems": "center", "gap": "4px"}, children=[
                            vs_logo,
                            dmc.Text(format_game_time(match.get('game_time', 0)), fw=600, size="md", c="dimmed", style={"marginTop": "8px"}),
                            dmc.Badge(lead_text, color=lead_color, variant="light")
                        ]),

                        html.Div(style={"flex": "1 1 0", "display": "flex", "alignItems": "center", "justifyContent": "flex-start", "gap": "16px"}, children=[
                            dmc.Text(f"{match.get('dire_score', 0)}", fw=800, size="3rem", c=COLORS['dire']),
                            dmc.Image(src=dire_logo, w=70, style={"borderRadius": "4px"}),
                            dmc.Text(f"{match.get('dire_name', 'Dire')}", fw=700, size="xl"),
                        ]),
                    ])
                ])
            ]),
            
            dmc.GridCol(span=12, children=[
                dmc.SimpleGrid(cols=2, spacing="md", children=[
                    dmc.Paper(withBorder=True, p="xs", children=[
                        dmc.Group([
                            dmc.Text("Radiant Quality", size="sm", c="dimmed"),
                            dmc.Text(f"Rating: {float(match.get('avg_radiant_rating') or 0):.0f} | Draft: {float(match.get('radiant_draft_score') or 0):.2f}", fw=600)
                        ], justify="space-between")
                    ]),
                    dmc.Paper(withBorder=True, p="xs", children=[
                        dmc.Group([
                            dmc.Text("Dire Quality", size="sm", c="dimmed"),
                            dmc.Text(f"Rating: {float(match.get('avg_dire_rating') or 0):.0f} | Draft: {float(match.get('dire_draft_score') or 0):.2f}", fw=600)
                        ], justify="space-between")
                    ]),
                ])
            ]),

            dmc.GridCol(span=12, children=[
                dmc.Paper(withBorder=True, p="xl", radius="md", children=[
                    dmc.Text("Kelly Criterion Calculator", fw=700, size="lg", style={"marginBottom": "20px"}),
                    dmc.Grid(gutter="xl", children=[
                        dmc.GridCol(span=12, children=[
                            dmc.Text("Model Win Prediction Probability", size="sm", fw=600, style={"marginBottom": "8px"}),
                            dmc.ProgressRoot(
                                size="xl",
                                radius="xl",
                                children=[
                                    dmc.ProgressSection(
                                        value=rad_prob * 100,
                                        color=COLORS['radiant'],
                                        children=dmc.ProgressLabel(f"Radiant: {rad_prob*100:.1f}%")
                                    ),
                                    dmc.ProgressSection(
                                        value=dire_prob * 100,
                                        color=COLORS['dire'],
                                        children=dmc.ProgressLabel(f"Dire: {dire_prob*100:.1f}%")
                                    )
                                ]
                            )
                        ]),
                        
                        dmc.GridCol(span=6, children=[
                            dmc.Card(withBorder=True, radius="md", p="md", style={"borderTop": f"4px solid {COLORS['radiant']}"}, children=[
                                dmc.Text("Radiant Betting Parameters", fw=600, size="md", c=COLORS['radiant'], mb="md"),
                                dmc.NumberInput(
                                    id="radiant-odds-input",
                                    label="Market Decimal Odds",
                                    description="Enter bookmaker price (e.g. 1.85)",
                                    min=1.01,
                                    max=50.0,
                                    step=0.01,
                                    value=2.00,
                                    mb="md"
                                ),
                                html.Div(id="radiant-kelly-output")
                            ])
                        ]),

                        dmc.GridCol(span=6, children=[
                            dmc.Card(withBorder=True, radius="md", p="md", style={"borderTop": f"4px solid {COLORS['dire']}"}, children=[
                                dmc.Text("Dire Betting Parameters", fw=600, size="md", c=COLORS['dire'], mb="md"),
                                dmc.NumberInput(
                                    id="dire-odds-input",
                                    label="Market Decimal Odds",
                                    description="Enter bookmaker price (e.g. 2.15)",
                                    min=1.01,
                                    max=50.0,
                                    step=0.01,
                                    value=2.00,
                                    mb="md"
                                ),
                                html.Div(id="dire-kelly-output")
                            ])
                        ]),
                        dmc.GridCol(span=12, children=[
                            dmc.Paper(withBorder=True, p="md", radius="md", style={"backgroundColor": "#2C2E33", "borderColor": "#e64980"}, children=[
                                dmc.Group(justify="space-between", children=[
                                    dmc.Stack(gap=0, children=[
                                        dmc.Text("Developer Action Console", fw=700, c="#e64980", size="sm"),
                                        dmc.Text("Save snapshot of current calculated metrics to database for post-game performance reporting.", size="xs", c="dimmed")
                                    ]),
                                    dmc.Button("Log Current Snapshot to DB", id="dev-save-analytics-btn", color="pink", variant="filled")
                                ]),
                                html.Div(id="dev-save-status-msg", style={"marginTop": "12px"})
                            ])
                        ]) if is_dev else None
                    ])
                ])
            ]),
        ])
    ])

@callback(
    Output("radiant-kelly-output", "children"),
    Output("dire-kelly-output", "children"),
    Input("radiant-odds-input", "value"),
    Input("dire-odds-input", "value"),
    State("live-match-probabilities", "data")
)
def update_betting_helpers(radiant_odds, dire_odds, cached_probs):
    if not cached_probs:
        return dash.no_update, dash.no_update
        
    rad_prob = cached_probs['rad_prob']
    dire_prob = cached_probs['dire_prob']

    rad_fraction = BettingHelper.kelly_criterion(float(radiant_odds), rad_prob)
    dire_fraction = BettingHelper.kelly_criterion(float(dire_odds), dire_prob)
    
    def build_output_ui(fraction, team_color):
        if fraction > 0:
            return dmc.Alert(
                children=[
                    dmc.Text(f"Advantage Detected! Value edge found.", size="xs", fw=500),
                    dmc.Text(f"Suggested Allocation: {fraction * 100:.2f}% of your bankroll.", size="sm", fw=700)
                ],
                title="BET RECOMMENDED",
                color="green",
                variant="light",
                style={"marginTop": "8px"}
            )
        else:
            return dmc.Alert(
                children=[
                    dmc.Text("No edge detected at these market price points. Pass on this line.", size="xs")
                ],
                title="NO ADVANTAGE",
                color="gray",
                variant="light",
                style={"marginTop": "8px"}
            )

    return build_output_ui(rad_fraction, COLORS['radiant']), build_output_ui(dire_fraction, COLORS['dire'])

@callback(
    Output("dev-save-status-msg", "children"),
    Input("dev-save-analytics-btn", "n_clicks"),
    State("radiant-odds-input", "value"),
    State("dire-odds-input", "value"),
    State("live-match-meta", "data"),
    State("live-match-probabilities", "data"),
    prevent_initial_call=True
)
def commit_kelly_snapshot_to_db(n_clicks, rad_odds, dire_odds, meta, probs):
    if not n_clicks or not meta or not probs:
        return dash.no_update
        
    match_id = meta['match_id']
    rad_prob, dire_prob = probs['rad_prob'], probs['dire_prob']
    
    rad_kelly = BettingHelper.kelly_criterion(rad_odds, rad_prob)
    dire_kelly = BettingHelper.kelly_criterion(dire_odds, dire_prob)
    
    insert_sql = """
        INSERT INTO public.live_match_bets_log 
        (match_id, radiant_odds, dire_odds, radiant_prob, dire_prob, radiant_kelly, dire_kelly)
        VALUES (:match_id, :rad_odds, :dire_odds, :rad_prob, :dire_prob, :rad_kelly, :dire_kelly);
    """
    
    try:
        db_manager.execute(insert_sql, params={
            'match_id': int(match_id),
            'rad_odds': float(rad_odds),
            'dire_odds': float(dire_odds),
            'rad_prob': float(rad_prob),
            'dire_prob': float(dire_prob),
            'rad_kelly': float(rad_kelly),
            'dire_kelly': float(dire_kelly)
        })
        
        return dmc.Alert(
            f"Snapshot recorded. Target Match: {match_id} | Radiant Edge: {rad_kelly*100:.1f}% | Dire Edge: {dire_kelly*100:.1f}%",
            title="Database Write Success", color="green", variant="filled"
        )
    except Exception as e:
        logging.error(f"Failed to log snapshot to DB: {str(e)}")
        return dmc.Alert(
            f"Failed to execute data query write: {str(e)}",
            title="Database Execution Error", color="red", variant="filled"
        )