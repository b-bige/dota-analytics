import pandas as pd
import numpy as np

import os, sys, logging

sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

from dota_db import DotaDB
from basic_logger import setup_logger
setup_logger(logfile_path='logs/historical_rating_db.log')

def main():
    db = DotaDB()
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

    # compute avg ratings per match per side in one go
    avg_ratings = df.groupby(['match_id', 'is_radiant'])['ordinal'].mean().unstack('is_radiant')
    avg_ratings.columns = ['avg_dire_rating', 'avg_radiant_rating']  # False=dire, True=radiant
    avg_ratings = avg_ratings.reset_index()

    # bulk update via execute_values
    rows = [
        (row['avg_radiant_rating'], row['avg_dire_rating'], row['match_id'])
        for _, row in avg_ratings.iterrows()
    ]
    rows = list(avg_ratings[['avg_radiant_rating', 'avg_dire_rating', 'match_id']].itertuples(index=False, name=None))

    db.query_executemany(
        '''
            UPDATE match_details SET
            avg_radiant_rating = %s,
            avg_dire_rating = %s
            WHERE id = %s 
        ''',
        params=rows
    )

if __name__ == '__main__':
    main()