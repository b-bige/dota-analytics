import pandas as pd
import numpy as np

import os, sys, logging
from datetime import datetime
sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))
from core.logger import setup_logger
setup_logger(logfile_path='logs/historical_rating_db.log')

from database import DatabaseManager

def main():
    """
    Updates the current ratings table based on the CSV produced by calculate_ratings.
    """
    db = DatabaseManager()
    idx = 1
    choices = {}
    for item in os.listdir('data'):
        if os.path.isfile(f'data/{item}'):
            if item.startswith('player_ratings'):
                print(f'{idx} - {item}')
                choices[idx] = item
                idx += 1
    selected = input('Select file: ')
    file = f'data/{choices[int(selected)]}'
    logging.info(f'Saving ratings from file: {file}')
    df = pd.read_csv(file)
    df['last_updated'] = datetime.now()
    db.insert_df_into_table(df, 'current_player_ratings', conflict_cols=['account_id'])

if __name__ == '__main__':
    main()