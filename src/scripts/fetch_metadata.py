import kagglehub
from pathlib import Path
import os
import sys

def fetch_metadata(month_number):
    project_root = os.path.abspath(os.path.join(Path(__file__), '../../..'))
    for i in range(1, month_number + 1):
        kagglehub.dataset_download('bwandowando/dota-2-pro-league-matches-2023', path=f'20260{i}/main_metadata.csv', output_dir=f'{project_root}/data/pro_matches_dataset')

if __name__ == '__main__':
    fetch_metadata(5)