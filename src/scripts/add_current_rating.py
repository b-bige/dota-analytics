import pandas as pd
import numpy as np

import os, sys

sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

from dota_db import DotaDB

def main():
    db = DotaDB()
    df = pd.read_csv('data/player_ratings_25_300.csv')
    db.create_table_from_df(df, 'current_player_ratings')
    db.insert_df_into_table(df, 'current_player_ratings', conflict_cols=['account_id'])

if __name__ == '__main__':
    main()