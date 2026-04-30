import pandas as pd
import numpy as np
import kagglehub

import os
import sys
sys.path.append(os.path.abspath('./src'))
from pathlib import Path

import logging
from core.logger import setup_logger
setup_logger('logs/fetch_dataset_update.log')

def fetch_dataset_update() -> dict:
    root_path = Path(kagglehub.dataset_download(handle='bwandowando/dota-2-pro-league-matches-2023', output_dir=f'{os.getcwd()}/data/'))
    storage = {}
    data_folders = list(root_path.rglob('20*/'))
    for folder in data_folders:
        data_files = list(folder.rglob('*.csv'))
        for file in data_files:
            if file.name not in storage.keys():
                storage[file.name] = pd.read_csv(file)
            else:
                storage[file.name] = pd.concat([storage[file.name], pd.read_csv(file)])
        logging.info(f'Folder for year {folder.name} finished')
    return storage
