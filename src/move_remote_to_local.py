import pandas as pd
import numpy as np
import os
import sys
sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

from db_functions import DotaDB

import logging
import basic_logger
basic_logger.setup_logger(logfile_path='logs/save_local_players.log')

def main(): #TODO: make generic
    db = DotaDB(schema='kaggle') 
    query = "SELECT COLUMN_NAME FROM information_schema.columns WHERE table_name = 'main_metadata'"
    table_columns = [c[0] for c in db.query_select(query)]
    df = db.query_select_to_df('SELECT * FROM main_metadata', columns=table_columns)
    db.set_local_or_remote(schema='public', local=True)
    db.create_table_from_df(df, 'main_metadata')
    db.insert_df_into_table(df, 'main_metadata')

if __name__ == '__main__':
    main()