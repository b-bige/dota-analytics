import pandas as pd
import numpy as np

import os, sys, logging

sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

from db_functions import DotaDB
from basic_logger import setup_logger
setup_logger(logfile_path='historical_rating_db.log')

def main():
    db = DotaDB()
    df = pd.read_csv('data/rating_history.csv').sort_values('match_id')
    df = df[df['match_id'] > 6200000000]

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