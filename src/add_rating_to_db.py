import pandas as pd
import numpy as np

import os, sys

sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

from db_functions import DotaDB

def main():
    db = DotaDB()
    df = pd.read_csv('data/player_ratings.csv')
    db.create_table_from_df(df, 'current_player_ratings')
    db.insert_df_into_table(df, 'current_player_ratings')

if __name__ == '__main__':
    main()