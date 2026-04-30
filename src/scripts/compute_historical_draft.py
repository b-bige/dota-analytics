import os
import sys
import logging
from typing import List, Optional

import numpy as np
import pandas as pd

sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

from database.dota_db import DotaDB
from core.logger import setup_logger

setup_logger(logfile_path='logs/historical_draft.log')


def map_match_times_to_patch_ids(patch_rows: List[tuple], match_times: np.ndarray) -> np.ndarray:
    """
    patch_rows: list of tuples (patch_id, asOfDateTime)
    match_times: numpy array of match start datetimes
    returns: numpy array of patch_id (or None) aligned with match_times
    """
    if len(patch_rows) == 0:
        return np.array([None] * len(match_times), dtype=object)

    patches_df = pd.DataFrame(patch_rows, columns=['patch_id', 'asOfDateTime'])
    patches_df = patches_df.sort_values('asOfDateTime').reset_index(drop=True)
    patch_times = patches_df['asOfDateTime'].to_numpy()
    patch_ids = patches_df['patch_id'].to_numpy()
    idx = np.searchsorted(patch_times, match_times, side='right') - 1
    mapped = np.where(idx >= 0, patch_ids[idx], None)
    return mapped


def process_batch(db: DotaDB, batch: List[int]) -> None:
    players_query = '''
        SELECT md.id AS match_id,
               mp."heroId" AS hero_id,
               mp."isRadiant" AS is_radiant,
               md."startDateTimeHuman" AS start_date_time
        FROM match_players mp
        JOIN match_details md ON mp.match_id = md.id
        WHERE mp.match_id = ANY(%s)
    '''
    players_df = db.select_to_df(players_query, params=(batch,),
                                 columns=['match_id', 'hero_id', 'is_radiant', 'start_date_time'])

    if players_df.empty:
        return

    match_start = (
        players_df.groupby('match_id', sort=False)['start_date_time']
        .first()
        .reset_index()
    )

    distinct_dates = match_start['start_date_time'].dropna().unique().tolist()
    if len(distinct_dates) == 0:
        match_start['patch_id'] = None
    else:
        patch_query = 'SELECT id, "asOfDateTime" FROM patches WHERE "asOfDateTime" < ANY(%s) ORDER BY "asOfDateTime"'
        patch_rows = db.select(patch_query, params=(distinct_dates,))
        match_times = match_start['start_date_time'].to_numpy()
        mapped_patch_ids = map_match_times_to_patch_ids(patch_rows, match_times)
        match_start['patch_id'] = mapped_patch_ids

    grouped = (
        players_df.groupby(['match_id', 'is_radiant'])['hero_id']
        .apply(list)
        .unstack(fill_value=[])
        .reset_index()
    ).rename(columns={False: 'dire_heroes', True: 'radiant_heroes'})

    merged = match_start.merge(grouped, on='match_id', how='left')
    if 'radiant_heroes' not in merged:
        merged['radiant_heroes'] = [[] for _ in range(len(merged))]
    if 'dire_heroes' not in merged:
        merged['dire_heroes'] = [[] for _ in range(len(merged))]

    rows = []
    for _, row in merged.iterrows():
        mid = int(row['match_id'])
        patch_id: Optional[int] = row.get('patch_id')
        # ensure lists (could be NaN if missing)
        radiant_list = row['radiant_heroes'] if isinstance(row['radiant_heroes'], list) else []
        dire_list = row['dire_heroes'] if isinstance(row['dire_heroes'], list) else []

        radiant_score = db.compute_draft_strength(radiant_list, dire_list, patch_id)
        dire_score = db.compute_draft_strength(dire_list, radiant_list, patch_id)
        rows.append((radiant_score, dire_score, mid))

    if rows:
        update_query = 'UPDATE match_details SET radiant_draft_score = %s, dire_draft_score = %s WHERE id = %s'
        db.query_executemany(query=update_query, params=rows)

def main():
    db = DotaDB()
    match_ids = [r[0] for r in db.select('SELECT id FROM match_details')]
    BATCH_SIZE = 1000
    total = len(match_ids)
    logging.info(f'Updating draft scores for {total} matches')

    for i in range(0, total, BATCH_SIZE):
        batch = match_ids[i:i + BATCH_SIZE]
        process_batch(db, batch)
        logging.info(f'Processed {min(i + BATCH_SIZE, total):,} / {total:,} matches...')

if __name__ == '__main__':
    main()
