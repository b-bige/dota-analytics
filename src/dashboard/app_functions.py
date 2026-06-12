import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from src.dashboard.theme import PLOTLY_LAYOUT, PLOTLY_COLORSCALES, COLORS
from src.database import engine, DatabaseManager
from src.dashboard.query_builder import QueryBuilder
from src.dashboard.filters import FILTER_MAP
from src.dashboard import db_manager
import time

##### Theming
def apply_fig_theme(fig: go.Figure):
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig

##### Helpers

def get_total_matches(clauses: str='', params=None):
    query = 'SELECT COUNT(id) FROM match_details md '
    if clauses:
        query += clauses
    return db_manager.select(query, params=params)[0][0]

def format_game_time(seconds: int) -> str:
    if not seconds:
        return "00:00"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"

##### Graphs

def fig_most_picked(qb: QueryBuilder, match_count):
    if not qb.is_filtered:
        results = db_manager.select(
            '''SELECT picks, "displayName" 
               FROM hero_pick_ban_stats 
               ORDER BY picks DESC LIMIT 5'''
        )
    else:
        qb.join('mpb', 'JOIN match_pick_bans mpb ON md.id = mpb.match_id')
        qb.join('hd_mpb', 'JOIN hero_details hd ON hd.id = mpb."heroId"')
        query, params = qb.build(
            select='COUNT(*) FILTER (WHERE mpb."isPick" = TRUE) AS count, hd."displayName"',
            extra_conditions='',
            order_by='GROUP BY hd."displayName" ORDER BY count DESC LIMIT 5'
        )
        results = db_manager.select(query, params=params)

    most_picked = pd.DataFrame(results, columns=['picks', 'hero']).sort_values('picks')
    most_picked['picks'] = (most_picked['picks'] / match_count).round(2) 
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=most_picked['picks'],
        y=most_picked['hero'],
        orientation='h',
        marker=dict(
            color=most_picked['picks'],
            colorscale=PLOTLY_COLORSCALES['colorscale'],
            showscale=False,
        ),
        text=[f"{picks:.0%}" for picks in most_picked['picks']],
        textposition='outside'
    ))
    fig = apply_fig_theme(fig)
    fig.update_layout(
        title="Top 5 picked heroes",
        autosize=True,
        xaxis=dict(title_text='Pick rate', tickformat=".0%", range=[0, max(most_picked['picks']) * 1.15], showgrid=False),
        yaxis=dict(showgrid=False)
    )
    return fig

def fig_most_banned(qb:QueryBuilder, match_count):
    if not qb.is_filtered:
        results = db_manager.select(
            '''SELECT bans, "displayName" 
               FROM hero_pick_ban_stats 
               ORDER BY bans DESC LIMIT 5'''
        )
    else:
        qb.join('mpb', 'JOIN match_pick_bans mpb ON md.id = mpb.match_id')
        qb.join('hd_mpb', 'JOIN hero_details hd ON hd.id = mpb."heroId"')
        query, params = qb.build(
            select='COUNT(*) FILTER (WHERE mpb."isPick" = FALSE) AS count, hd."displayName"',
            order_by='GROUP BY hd."displayName" ORDER BY count DESC LIMIT 5'
        )
        results = db_manager.select(query, params=params)

    most_banned = pd.DataFrame(results, columns=['bans', 'hero']).sort_values('bans')
    most_banned['bans'] = (most_banned['bans'] / match_count).round(2) 
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=most_banned['bans'],
        y=most_banned['hero'],
        orientation='h',
        marker=dict(
            color=most_banned['bans'],
            colorscale=PLOTLY_COLORSCALES['colorscale'],
            showscale=False,
        ),
        text=[f"{bans:.0%}" for bans in most_banned['bans']],
        textposition='outside'
    ))
    fig = apply_fig_theme(fig)
    fig.update_layout(
        title="Top 5 banned heroes",
        autosize=True,
        xaxis=dict(title_text='Ban rate', tickformat=".0%", range=[0, max(most_banned['bans']) * 1.15], showgrid=False),
        yaxis=dict(showgrid=False)
    )
    return fig

def fig_top_winrate(qb: QueryBuilder, match_count):
    min_picks = max(2, match_count // 10)
    if not qb.is_filtered:
        results = db_manager.select(
            '''SELECT winrate, picks, "displayName"
               FROM hero_winrate_stats
               WHERE picks >= :min_picks
               ORDER BY winrate DESC LIMIT 5''',
            params={'min_picks': min_picks}
        )
    else:
        qb.join('mp', 'JOIN match_players mp ON mp.match_id = md.id')
        qb.join('hd', 'JOIN hero_details hd ON mp."heroId" = hd.id')
        qb.having('COUNT(*) >= :min_picks', {'min_picks': min_picks})
        query, params = qb.build(
            select='AVG(CAST(mp."isVictory" AS INT)) AS winrate, COUNT(*) as picks, hd."displayName"',
            group_by='GROUP BY hd."displayName"',
            order_by='ORDER BY winrate DESC LIMIT 5'
        )
        results = db_manager.select(query, params=params)

    winrates = (pd.DataFrame(results, columns=['winrate', 'picks', 'hero'])
                .convert_dtypes()
                .sort_values('winrate'))
    winrates['winrate'] = winrates['winrate'].astype('Float32').round(2)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=winrates['winrate'],
        y=winrates['hero'],
        orientation='h',
        marker=dict(
            color=winrates['winrate'],
            colorscale=PLOTLY_COLORSCALES['colorscale'],
            showscale=False,
        ),
        customdata=winrates['picks'],
        text=[f"{w:.0%}" for w in winrates['winrate']],
        textposition='outside'
    ))
    fig = apply_fig_theme(fig)
    fig.update_layout(
        title="Top 5 heroes by winrate",
        autosize=True,
        xaxis=dict(title_text='Winrate', tickformat=".0%",
                   range=[0, max(winrates['winrate']) * 1.15], showgrid=False),
        yaxis=dict(showgrid=False)
    )
    return fig

def fig_most_present(qb: QueryBuilder, match_count):
    if not qb.is_filtered:
        results = db_manager.select(
            '''SELECT presence, "displayName" 
               FROM hero_presence_stats
               ORDER BY presence DESC LIMIT 5'''
        )
    else:
        qb.join('mpb', 'JOIN match_pick_bans mpb ON md.id = mpb.match_id')
        qb.join('hd_mpb', 'JOIN hero_details hd ON hd.id = mpb."heroId"')
        query, params = qb.build(
            select='COUNT(*) AS presence, hd."displayName"',
            order_by='GROUP BY hd."displayName" ORDER BY presence DESC LIMIT 5'
        )
        results = db_manager.select(query, params=params)
    most_present = pd.DataFrame(results, columns=['presence', 'hero']).sort_values('presence')
    most_present['presence'] = (most_present['presence'] / match_count).round(2)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=most_present['presence'],
        y=most_present['hero'],
        orientation='h',
        marker=dict(
            color=most_present['presence'],
            colorscale=PLOTLY_COLORSCALES['colorscale'],
            showscale=False,
        ),
        text=[f"{pres:.0%}" for pres in most_present['presence']],
        textposition='outside'
    ))
    fig = apply_fig_theme(fig)
    fig.update_layout(
        title="Top 5 present heroes",
        autosize=True,
        xaxis=dict(title_text='Presence rate', tickformat=".0%", range=[0, max(most_present['presence']) * 1.15], showgrid=False),
        yaxis=dict(showgrid=False)
    )
    return fig

def fig_duration_hist(qb: QueryBuilder):
    query, params = qb.build(select='"durationSeconds" / 60 AS duration_minutes')
    df = db_manager.select_to_df(query, params)
    n_matches = len(df)
    if n_matches < 30:
        df['count'] = 1
        
        fig = px.strip(
            df, 
            x='duration_minutes',
            title="Match duration distribution (Individual matches)",
            template='plotly_white',
            stripmode='group'
        )
        fig = apply_fig_theme(fig)
        fig.update_traces(
            hovertemplate="Duration: %{x:f} minutes<br>"
        )
        fig.update_yaxes(
            showgrid=False,
            zeroline=False,
            showticklabels=False
        )
        fig.update_layout(
            xaxis_title="Match Duration (Minutes)",
            yaxis_title="Number of Matches",
            bargap=0.4 # Slightly wider gap for small sets to make them distinct
        )
        return fig
    min_val = df['duration_minutes'].min()
    max_val = df['duration_minutes'].max()
    data_range = max_val - min_val
    if data_range == 0:
        data_range = 10
    target_bins = 30
    bin_size = max(1, round(data_range / target_bins))
    bins = np.arange(np.floor(min_val), np.ceil(max_val) + bin_size, bin_size)
    fig = px.histogram(df, nbins=len(bins), color_discrete_sequence=[COLORS['primary']])
    fig = apply_fig_theme(fig)
    fig.update_traces(xbins=dict(
        start=bins[0],
        end=bins[-1],
        size=bin_size
    ))
    fig.update_traces(
        patch={
            'marker': dict(
                showscale=False,
                line=dict(
                    color=COLORS['bg_elevated'], 
                    width=1
                )
            )
        }
    )
    fig.update_layout(
        title="Match duration distribution",
        autosize=True,
        xaxis=dict(showgrid=False, title_text='Match Duration (Minutes)', ticksuffix='m'),
        yaxis=dict(showgrid=False, title_text='Number of Matches'),
        showlegend=False
    )
    return fig

def fig_gpm_volatility(qb: QueryBuilder, hero_list: list):
    qb.join('mp', 'JOIN match_players mp ON mp.match_id = md.id')
    qb.join('hd', 'JOIN hero_details hd ON mp."heroId" = hd.id')
    qb.where('hd."displayName" = ANY(:hero_list)', {'hero_list': hero_list})
    query, params = qb.build(select='hd.id as hero_id, hd."displayName" as hero_name, mp."goldPerMinute" as gpm')
    results = db_manager.select(query, params=params)
    df = pd.DataFrame(results, columns=['hero_id', 'hero_name', 'gpm'])
    fig = go.Figure()
    fig.add_trace(go.Box(
        x=df['hero_name'],
        y=df['gpm'],
        marker=dict(color=COLORS['primary'])
    ))
    fig = apply_fig_theme(fig)
    fig.update_layout(
        title="Gold Per Minute Volatility",
        autosize=True,
        xaxis=dict(title_text='Hero', showgrid=False),
        yaxis=dict(showgrid=False)
    )
    return fig

def fig_greed_plot(qb: QueryBuilder, position):
    position_map = {
        'Carry': 'POSITION_1',
        'Midlaner': 'POSITION_2',
        'Offlaner': 'POSITION_3',
        'Roamer/Soft Support': 'POSITION_4',
        'Hard Support': 'POSITION_5'
    }
    
    # 1. Define the SQL query using the WIDTH_BUCKET approach
    query = """
        SELECT 
            WIDTH_BUCKET(networth_share, 0, 0.40, 6) AS bucket_index,
            AVG(CAST("isVictory" AS INT)) AS winrate,
            COUNT(*) AS games
        FROM mv_match_networth_shares
        WHERE position = :pos_filter
        GROUP BY bucket_index
        ORDER BY bucket_index;
    """
    
    # Execute with position parameter bound
    params = {'pos_filter': position_map[position]}
    results = db_manager.select(query, params=params)
    
    # Map the numeric buckets back to categorical labels
    winrate_by_share = pd.DataFrame(results, columns=['bucket_index', 'winrate', 'games'])
    
    # Map the index to your standard UI buckets
    bucket_labels = {
        1: '<15%',
        2: '15-20%',
        3: '20-25%',
        4: '25-30%',
        5: '30-35%',
        6: '35-40%',
        7: '>40%' # Handles values above the 0.40 upper bound
    }
    
    winrate_by_share['share_bucket'] = winrate_by_share['bucket_index'].map(bucket_labels)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=winrate_by_share['share_bucket'].astype(str),
        y=winrate_by_share['winrate'],
        marker=dict(
            color=winrate_by_share['winrate'],
            colorscale=PLOTLY_COLORSCALES['colorscale'],
            showscale=False,
        ),
        customdata=winrate_by_share['games'],
        text=[f"{w:.0%}" for w in winrate_by_share['winrate']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Win Rate: %{y:.1%}<br>Games: %{customdata}<extra></extra>'
    ))
    fig = apply_fig_theme(fig)
    fig.add_hline(y=0.5, line_dash='dash', line_color=COLORS['text_muted'])
    fig.update_layout(
        title=f'{position} Win Rate by Networth Share',
        xaxis=dict(title_text='Networth Share', showgrid=False),
        yaxis=dict(title_text='Win Rate', tickformat='.0%', showgrid=False, range=[0, 0.8]),
        autosize=True
    )
    return fig

#### Update helpers
def update_url_from_filters_helper(params, filters):
    for filter_name, value in filters.items():
        params.update(FILTER_MAP[filter_name].to_url_params(value))
    return params

if __name__ == '__main__':
    fig_greed_plot(QueryBuilder(), 'Carry')