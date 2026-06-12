from src.database import DatabaseManager
from src.api import OpenDotaClient
from src.analytics import RatingSystem
import logging
from src.core.logger import setup_logger
import pandas as pd
import itertools

setup_logger(logfile_path='logs/update_database.log')

def fetch_finished_live():
    #NOTE: Using an interval of 180 minutes from the current timestamp as a buffer
    # to let still ongoing matches finish in order to keep rating and player state updates chronological
    db = DatabaseManager()
    odc = OpenDotaClient()
    rs = RatingSystem(db_manager=db)
    query = '''
        SELECT 
            match_id, 
            start_date_time,
            status, 
            radiant_draft_score, 
            dire_draft_score, 
            avg_radiant_rating, 
            avg_dire_rating,
            rad_win_predicted
        FROM live_matches 
        WHERE start_date_time <= NOW() - INTERVAL '180 minutes' 
        ORDER BY start_date_time ASC
    '''
    live_data = db.select_to_df(query)
    live_ids = list(live_data['match_id'])
    BATCH_SIZE = 100
    for i in range(0, len(live_ids), BATCH_SIZE):
        batch_ids = live_ids[i:i + BATCH_SIZE]
        finished_data = odc.get_multiple_matches(batch_ids, db_manager=db)
        for table_name, table_data in finished_data.items():
            df = pd.DataFrame(table_data)
            if table_name == 'match_details':
                batch_data = live_data[live_data['match_id'].isin(batch_ids)].copy()
                df = pd.merge(
                    left=df,
                    right=batch_data[
                        [
                            'match_id', 
                            'radiant_draft_score', 
                            'dire_draft_score', 
                            'avg_radiant_rating', 
                            'avg_dire_rating',
                            'rad_win_predicted'
                        ]
                    ],
                    left_on='id',
                    right_on='match_id',
                    how='inner'
                ).drop(columns=['match_id'])
            db.insert_df_into_table(df, table_name, conflict_cols=['id'])
        for mid in batch_ids:
                rs.update_ratings_from_match(mid)
        players = pd.DataFrame(finished_data['match_players'])
        for j in range(len(finished_data['match_details'])):
            match_details = finished_data['match_details'][j]
            match_players = players[players['match_id'] == match_details['id']]
            update_analytical_managers(match_details, match_players, db)
        db.execute('DELETE FROM live_matches WHERE match_id = ANY(:batch_ids)', params={'batch_ids': batch_ids})
        logging.info(f"Finished {i} matches out ouf {len(live_ids)}")

def update_analytical_managers(match_details, players, db_manager: DatabaseManager):
    """
    Updates the State and Player analytical tracking tables using Pandas DataFrames
    and fast PostgreSQL COPY upserts.
    """

    patch_id = match_details['gameVersionId']
    radiant_win = match_details['didRadiantWin']

    radiant_players = players[players['isRadiant']]
    dire_players = players[~players['isRadiant']]

    radiant_heroes = list(radiant_players['heroId'])
    dire_heroes = list(dire_players['heroId'])

    state_records = []

    def add_state(stype, k_a, k_b, is_win):
        state_records.append({
            'stat_type': stype,
            'key_a': k_a,
            'key_b': k_b,
            'wins': 1 if is_win else 0,
            'games': 1
        })

    for h in radiant_heroes: add_state('hero', h, -1, radiant_win)
    for h in dire_heroes: add_state('hero', h, -1, not radiant_win)

    for h1, h2 in itertools.combinations(sorted(radiant_heroes), 2):
        add_state('synergy', h1, h2, radiant_win)
    for h1, h2 in itertools.combinations(sorted(dire_heroes), 2):
        add_state('synergy', h1, h2, not radiant_win)

    for rh in radiant_heroes:
        for dh in dire_heroes:
            add_state('matchup', rh, dh, radiant_win)
            add_state('matchup', dh, rh, not radiant_win)

    df_state = pd.DataFrame(state_records)

    player_records = []
    for _, p in players.iterrows():
        acc_id = p['steamAccountId']
        if acc_id and acc_id > 0: 
            player_records.append({
                'account_id': acc_id,
                'hero_id': p['heroId'],
                'wins': 1 if p['isVictory'] else 0,
                'games': 1
            })
            
    df_player = pd.DataFrame(player_records)
    meta_query = "SELECT current_major_patch FROM state_manager_meta ORDER BY id DESC LIMIT 1;"
    meta_df = db_manager.select_to_df(meta_query)
    current_major_patch = meta_df.iloc[0]['current_major_patch'] if not meta_df.empty else patch_id
    active_queue_pos = 0 

    if not df_state.empty:
        df_state_stats_sub = df_state.copy()
        df_state_stats_sub['scope'] = 'sub_patch'
        
        df_state_stats_major = df_state.copy()
        df_state_stats_major['scope'] = 'major_patch'
        
        df_state_stats = pd.concat([df_state_stats_sub, df_state_stats_major], ignore_index=True)

        db_manager.insert_df_into_table(
            df=df_state_stats,
            table_name='state_manager_stats',
            conflict_cols=['scope', 'stat_type', 'key_a', 'key_b'],
            increment_cols=['wins', 'games'] 
        )

        db_manager.insert_df_into_table(
            df=df_state,
            table_name='state_manager_history',
            conflict_cols=['stat_type', 'key_a', 'key_b'],
            increment_cols=['wins', 'games']
        )

        df_state_queue = df_state.copy()
        df_state_queue['queue_position'] = active_queue_pos
        df_state_queue['major_patch'] = current_major_patch
        
        db_manager.insert_df_into_table(
            df=df_state_queue,
            table_name='state_manager_queue',
            conflict_cols=['queue_position', 'stat_type', 'key_a', 'key_b'],
            increment_cols=['wins', 'games']
        )

    if not df_player.empty:
        df_player_stats_sub = df_player.copy()
        df_player_stats_sub['scope'] = 'sub_patch'
        df_player_stats_sub['patch'] = patch_id
        
        df_player_stats_major = df_player.copy()
        df_player_stats_major['scope'] = 'major_patch'
        df_player_stats_major['patch'] = patch_id
        
        df_player_stats = pd.concat([df_player_stats_sub, df_player_stats_major], ignore_index=True)

        db_manager.insert_df_into_table(
            df=df_player_stats,
            table_name='player_manager_stats',
            conflict_cols=['scope', 'account_id', 'hero_id', 'patch'],
            increment_cols=['wins', 'games']
        )

        db_manager.insert_df_into_table(
            df=df_player,
            table_name='player_manager_history',
            conflict_cols=['account_id', 'hero_id'],
            increment_cols=['wins', 'games']
        )

        df_player_queue = df_player.copy()
        df_player_queue['queue_position'] = active_queue_pos
        df_player_queue['major_patch'] = current_major_patch
        
        db_manager.insert_df_into_table(
            df=df_player_queue,
            table_name='player_manager_queue',
            conflict_cols=['account_id', 'hero_id', 'queue_position'],
            increment_cols=['wins', 'games']
        )

    logging.info(f"Successfully updated analytical state for match {match_details['id']}")

if __name__ == '__main__':
    fetch_finished_live()