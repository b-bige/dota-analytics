import pandas as pd
import numpy as np
from openskill.models import PlackettLuce

import os, sys, logging

sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

from database.dota_db import DotaDB
from core.logger import setup_logger

listener = setup_logger(logfile_path='logs/calculate_rating.log')
log = logging.getLogger(__name__)
db = DotaDB()

raw_tau = input('Enter TAU (default 0.25): ')
TAU = float(raw_tau) if raw_tau else 0.25
model = PlackettLuce(tau=TAU)

player_ratings = {}
rating_history = []
next_anon_id = 0


def main():
    global next_anon_id
    log.info(
        f'Starting rating calculation with tau: {TAU}'
    )
    
    log.info("Loading metadata...")
    metadata = db.select_to_df('SELECT * FROM match_details', table='match_details')
    metadata = metadata.sort_values(by='startDateTimeHuman', ascending=True).reset_index(drop=True)

    radiant_win_lookup = dict(zip(metadata['id'], metadata['didRadiantWin']))

    valid_mids = [
        mid[0] for mid in db.select(
            '''SELECT match_id AS players
                FROM match_players
                GROUP BY match_id
                HAVING COUNT(DISTINCT "heroId") = 10;'''
        )
    ]
    log.info(f"{len(valid_mids):,} matches have correct player data.")

    BATCH_SIZE = 1000
    total = len(valid_mids)
    for i in range(0, total, BATCH_SIZE):
        batch = valid_mids[i:i + BATCH_SIZE]
        players_df = db.select_to_df(
            'SELECT * FROM match_players WHERE match_id = ANY(%s)',
            params=(batch,),
            table='match_players'
        )
        for match_id, group in players_df.groupby('match_id'):
            radiant_win = radiant_win_lookup.get(match_id)

            if radiant_win is None:
                log.warning(f"Match {match_id} not found in metadata, skipping.")
                continue

            process_match(match_id, group, radiant_win)

        log.info(f"Processed {min(i + BATCH_SIZE, total):,} / {total:,} matches...")

    log.info("Saving results...")

    final_ratings = pd.DataFrame([
        {
            'account_id': pid,
            'mu':         r.mu,
            'sigma':      r.sigma,
            'ordinal':    r.ordinal(),
        }
        for pid, r in player_ratings.items()
        if not isinstance(pid, str)
    ]).sort_values('ordinal', ascending=False)

    history_df = pd.DataFrame(rating_history)

    final_ratings.to_csv(f'data/player_ratings_tau_{TAU}.csv', index=False)
    history_df.to_csv(f'data/rating_history_tau_{TAU}.csv', index=False)

    log.info(f"Done. Rated {len(final_ratings):,} unique players.")
    log.info(f"Rating history: {len(history_df):,} entries.")


def get_or_create_player_id(account_id, match_id, hero_id):
    """
    Returns existing account_id if valid, otherwise creates and returns a new anonymous ID.
    Also initializes the player in player_ratings if not already present.
    """
    global next_anon_id
    
    if pd.isna(account_id) or account_id <= 0:
        anon_id = f'anon_{match_id}_{hero_id}'
        next_anon_id += 1
    else:
        anon_id = int(account_id)
    
    if anon_id not in player_ratings:
        player_ratings[anon_id] = model.rating()
    
    return anon_id


def process_match(match_id, players_df, radiant_win):
    """
    Process a single match: append to rating history, calculate ratings, update player ratings.
    """
    radiant = players_df[players_df['isRadiant'] == True].copy()
    dire = players_df[players_df['isRadiant'] == False].copy()

    if len(radiant) == 0 or len(dire) == 0:
        return

    # Get or create player IDs for all players in the match
    radiant_ids = []
    for _, row in radiant.iterrows():
        pid = get_or_create_player_id(row['steamAccountId'], match_id, row['heroId'])
        radiant_ids.append(pid)

    dire_ids = []
    for _, row in dire.iterrows():
        pid = get_or_create_player_id(row['steamAccountId'], match_id, row['heroId'])
        dire_ids.append(pid)

    # Get current ratings before update
    radiant_ratings = [player_ratings[pid] for pid in radiant_ids]
    dire_ratings = [player_ratings[pid] for pid in dire_ids]

    # Append to rating history (before update)
    for pid, r in zip(radiant_ids, radiant_ratings):
        if not isinstance(pid, str):
            rating_history.append({
                'account_id': pid,
                'match_id': match_id,
                'is_radiant': True,
                'mu': r.mu,
                'sigma': r.sigma,
                'ordinal': r.ordinal(),
            })
    
    for pid, r in zip(dire_ids, dire_ratings):
        if not isinstance(pid, str):
            rating_history.append({
                'account_id': pid,
                'match_id': match_id,
                'is_radiant': False,
                'mu': r.mu,
                'sigma': r.sigma,
                'ordinal': r.ordinal(),
            })

    # Update ratings based on match outcome
    if radiant_win:
        new_radiant, new_dire = model.rate([radiant_ratings, dire_ratings])
    else:
        new_dire, new_radiant = model.rate([dire_ratings, radiant_ratings])

    # Update player ratings dictionary
    for pid, new_r in zip(radiant_ids + dire_ids, new_radiant + new_dire):
        player_ratings[pid] = new_r


if __name__ == '__main__':
    main()