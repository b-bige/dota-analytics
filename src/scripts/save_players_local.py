import pandas as pd
import numpy as np
import os
import sys
sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

from database.dota_db import DotaDB

import logging
import core.logger as logger
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
logger.setup_logger(logfile_path=f'{str(PROJECT_PATH)}/logs/save_local_players.log')

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS player_match_stats (
    match_id            BIGINT,
    account_id          BIGINT,
    hero_id             INT,
    player_slot         INT,
    start_time          BIGINT,
    duration            INT,
    radiant_win         BOOLEAN,
    is_radiant          BOOLEAN,
    win                 INT,
    patch               INT,
    leagueid            BIGINT,
    region              INT,
    rank_tier           INT,
    lobby_type          INT,
    game_mode           INT,
    lane_role           INT,
    lane                INT,
    is_roaming          BOOLEAN,
    gold_per_min        FLOAT,
    xp_per_min          FLOAT,
    kills               INT,
    deaths              INT,
    assists             INT,
    last_hits           INT,
    denies              INT,
    net_worth           FLOAT,
    hero_damage         FLOAT,
    tower_damage        FLOAT,
    hero_healing        FLOAT,
    kda                 FLOAT,
    kills_per_min       FLOAT,
    lane_efficiency_pct FLOAT,
    obs_placed          INT,
    sen_placed          INT,
    stuns               FLOAT,
    camps_stacked       INT,
    creeps_stacked      INT,
    teamfight_participation FLOAT,
    observer_kills      INT,
    sentry_kills        INT,
    actions_per_min     FLOAT,
    level               INT,
    roshan_kills        INT,
    tower_kills         INT,
    neutral_kills       INT,
    buyback_count       INT,
    benchmarks          JSONB
);
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pms_account_id ON player_match_stats(account_id);",
    "CREATE INDEX IF NOT EXISTS idx_pms_match_id   ON player_match_stats(match_id);",
    "CREATE INDEX IF NOT EXISTS idx_pms_start_time ON player_match_stats(start_time);",
    "CREATE INDEX IF NOT EXISTS idx_pms_leagueid   ON player_match_stats(leagueid);",
]

KEEP_COLUMNS = [
    # Identity
    'match_id',
    'account_id',
    'hero_id',
    'player_slot',
 
    # Match context
    'start_time',
    'duration',
    'radiant_win',
    'isRadiant',
    'win',
    'patch',
    'leagueid',
    'region',
    'rank_tier',
    'lobby_type',
    'game_mode',
 
    # Role / lane
    'lane_role',
    'lane',
    'is_roaming',
 
    # Core performance — carry metrics
    'gold_per_min',
    'xp_per_min',
    'kills',
    'deaths',
    'assists',
    'last_hits',
    'denies',
    'net_worth',
    'hero_damage',
    'tower_damage',
    'hero_healing',
    'kda',
    'kills_per_min',
    'lane_efficiency_pct',
 
    # Support metrics
    'obs_placed',
    'sen_placed',
    'stuns',
    'camps_stacked',
    'creeps_stacked',
    'teamfight_participation',
    'observer_kills',
    'sentry_kills',
 
    # Other useful
    'actions_per_min',
    'level',
    'roshan_kills',
    'tower_kills',
    'neutral_kills',
    'buyback_count',
 
    # Benchmarks — pre-computed OpenDota percentiles, critical for scoring
    'benchmarks',
]
INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pms_account_id ON player_match_stats(account_id);",
    "CREATE INDEX IF NOT EXISTS idx_pms_match_id   ON player_match_stats(match_id);",
    "CREATE INDEX IF NOT EXISTS idx_pms_start_time ON player_match_stats(start_time);",
    "CREATE INDEX IF NOT EXISTS idx_pms_leagueid   ON player_match_stats(leagueid);",
]

def main():
    ## Database, table and index setup
    db = DotaDB(local=True)
    db.query_execute(CREATE_TABLE_SQL)
    for sql in INDEX_SQL:
        db.query_execute(sql)

    ## Saving of data
    for year in range(2016, 2026):
        save_details(db, folder=str(year))
    save_details(db, '202601')
    save_details(db, '202602')

def save_details(db:DotaDB, folder):
    df = pd.read_csv(
        filepath_or_buffer=f'data/{folder}/players.csv',
        usecols=lambda c: c in KEEP_COLUMNS    
    ).rename(columns={'isRadiant': 'is_radiant'})
    missing_acc_rows = len(df[df['account_id'].isna()])
    if missing_acc_rows != 0:
        logging.warning(f'Found {missing_acc_rows} rows without account ID')
    invalid_acc_rows = len(df[df['account_id'] <= 0])
    if invalid_acc_rows != 0:
        logging.warning(f'Found {invalid_acc_rows} rows with invalid account ID')
    db.insert_df_into_table(df, 'player_match_stats', jsonb_cols=['benchmarks'])

if __name__ == '__main__':
    main()