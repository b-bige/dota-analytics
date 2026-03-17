import httpx
import os
import sys
import json

sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

from db_functions import DotaDB

def main():
    db = DotaDB()
    with open('match_ids.json', 'r') as file:
        match_ids = json.load(file)
    
    with httpx.Client() as client:
        for match_id in match_ids:
            result = db.query_opendota(client, endpoint=f'matches/{match_id}')
            with open('result_example.json', 'w') as file:
                json.dump(result, file, indent=4)
            break

if __name__ == '__main__':
    main()