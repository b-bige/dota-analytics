import pandas as pd
import numpy as np

import os, sys, logging

sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

from database import DatabaseManager
from core.logger import setup_logger
setup_logger(logfile_path='logs/historical_rating_db.log')

def main():
    """
    Calculates team averages and updates the database based on the CSV produced by calculate_ratings.
    """
    db = DatabaseManager()
    idx = 1
    choices = {}
    for item in os.listdir('data'):
        if os.path.isfile(f'data/{item}'):
            if item.startswith('rating_history'):
                print(f'{idx} - {item}')
                choices[idx] = item
                idx += 1
    selected = input('Select file: ')
    file = f'data/{choices[int(selected)]}'
    logging.info(f'Saving ratings from file: {file}')
    df = pd.read_csv(file).sort_values('match_id')

    avg_ratings = df.groupby(['match_id', 'is_radiant'])['ordinal'].mean().unstack('is_radiant')
    avg_ratings.columns = ['avg_dire_rating', 'avg_radiant_rating']  
    avg_ratings = avg_ratings.reset_index()

    params = avg_ratings[['match_id', 'avg_radiant_rating', 'avg_dire_rating']].to_dict('records')
    db.execute_many(
        '''
            UPDATE match_details SET
            avg_radiant_rating = :avg_radiant_rating,
            avg_dire_rating = :avg_dire_rating
            WHERE id = :match_id
        ''',
        params=params
    )
    db.insert_df_into_table(df, 'rating_history')

if __name__ == '__main__':
    main()