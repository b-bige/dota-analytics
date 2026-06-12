from pathlib import Path
import os
import sys
import pandas as pd
from src.api import OpenDotaClient
from src.database import DatabaseManager
import time
import logging
from src.core import logger
logger.setup_logger(logfile_path='logs/fetch_game_from_metadata.log')

def fetch_game_from_metadata(month_number):
    project_root = os.path.abspath(os.path.join(Path(__file__), '../../..'))
    db = DatabaseManager()
    dataset_mids = get_dataset_match_ids(project_root, month_number)
    database_mids = get_database_match_ids(db)
    missing_ids = dataset_mids - database_mids
    odc = OpenDotaClient()
    master_storage = {
        'match_details': [],
        'match_death_events': [],
        'match_pick_bans': [],
        'match_tower_deaths': [],
        'match_players': [],
        'match_purchases': [],
        'match_runes': [],
        'match_wards': []
    }
    for idx, match_id in enumerate(list(missing_ids)):
        try:
            match_data = odc.get_match(match_id, db_manager=db)
            for table, records in match_data.items():
                if table == 'match_details':
                    master_storage['match_details'].append(records)
                else:
                    master_storage[table].extend(records)
        except Exception as e:
            logging.error(f"Failed to process match {match_id}: {e}")
        if idx % 60 == 0 and idx != 0:
            for table_name, table_data in master_storage.items():
                df = pd.DataFrame(table_data)
                db.insert_df_into_table(df, table_name, conflict_cols=['id'])
            master_storage.clear()
            master_storage = {
                'match_details': [],
                'match_death_events': [],
                'match_pick_bans': [],
                'match_tower_deaths': [],
                'match_players': [],
                'match_purchases': [],
                'match_runes': [],
                'match_wards': []
            }
    for table_name, table_data in master_storage.items():
        df = pd.DataFrame(table_data)
        db.insert_df_into_table(df, table_name, conflict_cols=['id'])

def get_dataset_match_ids(project_root, month_number):
    match_ids = set()
    for i in range(1, month_number + 1):
        metadata = pd.read_csv(f'{project_root}/data/pro_matches_dataset/20260{i}/main_metadata.csv')
        match_ids = match_ids | set(metadata['match_id'])
    return match_ids

def get_database_match_ids(db: DatabaseManager):
    query = 'SELECT id FROM match_details'
    match_ids = {r[0] for r in db.select(query)}
    return match_ids

if __name__ == '__main__':
    fetch_game_from_metadata(month_number=5)