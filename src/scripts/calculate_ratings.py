import pandas as pd
import numpy as np
from openskill.models import PlackettLuce

import os, sys, logging

sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

from database import DatabaseManager
from core.logger import setup_logger

listener = setup_logger(logfile_path='logs/calculate_rating.log')
log = logging.getLogger(__name__)
db = DatabaseManager()

raw_tau = input('Enter TAU (default 0.25): ')
TAU = float(raw_tau) if raw_tau else 0.25
model = PlackettLuce(tau=TAU)

player_ratings = {}
rating_history = []

def main():
    """
    Recalculates rating and saves them as two distinct CSVs:
    - player_ratings: current ratings for the players
    - rating_history: the ratings for players before each match
    Used to apply different rating model setups to retrain models.
    """
    log.info(
        f'Starting rating calculation with tau: {TAU}'
    )
    query = ''' 
        SELECT id, "startDateTimeHuman", "didRadiantWin" 
        FROM match_details 
        WHERE id IN (
            SELECT match_id 
            FROM match_players 
            GROUP BY match_id
            HAVING COUNT(DISTINCT "heroId") = 10
        )
        ORDER BY "startDateTimeHuman" ASC;
    '''
    log.info("Loading metadata...")
    metadata = db.select_to_df(query)


    BATCH_SIZE = 1000
    total = len(metadata)
    for i in range(0, total, BATCH_SIZE):
        batch_meta = metadata.iloc[i:i + BATCH_SIZE]
        batch_ids = batch_meta['id'].tolist()
        radiant_win_lookup = {int(k): v for k, v in zip(batch_meta['id'], batch_meta['didRadiantWin'])}

        players_df = db.select_to_df(
            '''
            SELECT match_id, "heroId", "isRadiant", "steamAccountId"
            FROM match_players 
            WHERE match_id = ANY(:match_ids)
            ''',
            params={'match_ids': batch_ids},
        )
        grouped = {match_id: group for match_id, group in players_df.groupby('match_id')}
        for match_id in batch_ids:
            group = grouped.get(match_id)
            if group is None or group.empty:
                log.warning(f"Match {match_id} not found in metadata, skipping.")
                continue
                
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
    if account_id is None or account_id <= 0:
        anon_id = f'anon_{match_id}_{hero_id}'
    else:
        anon_id = int(account_id)
    
    if anon_id not in player_ratings:
        player_ratings[anon_id] = model.rating()
    
    return anon_id

def process_match(match_id, players_df, radiant_win):
    """
    Process a single match: append to rating history, calculate ratings, update player ratings.
    """
    players = players_df.to_dict('records')
    
    radiant_records = [p for p in players if p['isRadiant']]
    dire_records = [p for p in players if not p['isRadiant']]

    if not radiant_records or not dire_records:
        return

    radiant_ids = [
        get_or_create_player_id(p['steamAccountId'], match_id, p['heroId']) 
        for p in radiant_records
    ]
    dire_ids = [
        get_or_create_player_id(p['steamAccountId'], match_id, p['heroId']) 
        for p in dire_records
    ]

    radiant_ratings = [player_ratings[pid] for pid in radiant_ids]
    dire_ratings = [player_ratings[pid] for pid in dire_ids]

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

    if radiant_win:
        new_radiant, new_dire = model.rate([radiant_ratings, dire_ratings])
        updated_ids = radiant_ids + dire_ids
        updated_ratings = new_radiant + new_dire
    else:
        new_dire, new_radiant = model.rate([dire_ratings, radiant_ratings])
        updated_ids = dire_ids + radiant_ids
        updated_ratings = new_dire + new_radiant

    for pid, new_r in zip(updated_ids, updated_ratings):
        player_ratings[pid] = new_r

if __name__ == '__main__':
    main()