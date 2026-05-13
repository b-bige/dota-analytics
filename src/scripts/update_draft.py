import logging
import pandas as pd
import numpy as np
from src.database.database_manager import DatabaseManager
from src.analytics import DraftService
from src.core import logger
logger.setup_logger(logfile_path='logs/historical_draft.log')

def main():
    """
    Recalculates draft scores and updates the database.
    Used when the calculation method was changed to retrain models.
    """
    db = DatabaseManager()
    ds = DraftService(db)
    match_rows = db.select('SELECT id FROM match_details')
    match_ids = [r[0] for r in match_rows]
    
    BATCH_SIZE = 1000
    total = len(match_ids)
    
    logging.info(f'Updating draft scores for {total:,} matches')

    for i in range(0, total, BATCH_SIZE):
        batch = match_ids[i:i + BATCH_SIZE]
        process_batch(db, ds, batch)
        logging.info(f'Processed {min(i + BATCH_SIZE, total):,} / {total:,} matches...')

def map_match_times_to_patch_ids(patch_rows: list[tuple], match_times: np.ndarray) -> np.ndarray:
    """
    patch_rows: list of tuples (patch_id, asOfDateTime)
    match_times: numpy array of match start datetimes
    returns: numpy array of patch_id (or None) aligned with match_times
    """
    if len(patch_rows) == 0:
        return np.array([None] * len(match_times), dtype=object)

    patches_df = pd.DataFrame(patch_rows, columns=['patch_id', 'asOfDateTime'])
    patches_df = patches_df.sort_values('asOfDateTime').reset_index(drop=True)
    patch_times_sorted = patches_df['asOfDateTime'].to_numpy()
    patch_ids = patches_df['patch_id'].to_numpy()
    
    idx = np.searchsorted(patch_times_sorted, match_times, side='right') - 1
    mapped = np.where(idx >= 0, patch_ids[idx], None)
    return mapped

def process_batch(db: DatabaseManager, ds: DraftService, batch: list[int]) -> None:
    """Processes a batch of matches and updates draft scores in the database."""
    winrate_map = ds._get_hero_stats() 
    synergy_map = ds._get_synergy_stats()
    counter_map = ds._get_counter_stats()
    players_query = '''
        SELECT md.id AS match_id,
               mp."heroId" AS hero_id,
               mp."isRadiant" AS is_radiant,
               md."startDateTimeHuman" AS start_date_time
        FROM match_players mp
        JOIN match_details md ON mp.match_id = md.id
        WHERE mp.match_id = ANY(:match_ids)
    '''
    
    players_df = db.select_to_df(players_query, params={'match_ids': batch})

    if players_df.empty:
        return

    players_df = players_df.replace({np.nan: None})

    match_start = (
        players_df.groupby('match_id', sort=False)['start_date_time']
        .first()
        .reset_index()
    )

    distinct_dates = match_start['start_date_time'].dropna().unique().tolist()
    
    if len(distinct_dates) == 0:
        match_start['patch_id'] = None
    else:
        patch_query = '''
            SELECT id, "asOfDateTime" 
            FROM patches 
            WHERE "asOfDateTime" < ANY(:dates) 
            ORDER BY "asOfDateTime"
        '''
        patch_rows = db.select(patch_query, params={'dates': distinct_dates})
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
        patch_id = row.get('patch_id')
        
        radiant_list = row['radiant_heroes'] if isinstance(row['radiant_heroes'], list) else []
        dire_list = row['dire_heroes'] if isinstance(row['dire_heroes'], list) else []
        radiant_score = ds.compute_draft_strength(
            radiant_list, 
            dire_list, 
            patch_id,
            stats_maps=(winrate_map, synergy_map, counter_map)
        )
        dire_score = ds.compute_draft_strength(
            dire_list, 
            radiant_list, 
            patch_id,
            stats_maps=(winrate_map, synergy_map, counter_map)
        )
        rows.append((radiant_score, dire_score, mid))

    if rows:
        update_query = '''
            UPDATE match_details 
            SET radiant_draft_score = :radiant_score, dire_draft_score = :dire_score 
            WHERE id = :match_id
        '''
        dict_params = [
            {
                "radiant_score": r[0],
                "dire_score": r[1],
                "match_id": r[2]
            }
            for r in rows
        ]
        db.execute_many(query=update_query, params=dict_params)

if __name__ == '__main__':
    main()