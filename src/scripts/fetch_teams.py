import pandas as pd
import numpy as np
import os
import sys
import httpx

sys.path.append(os.path.abspath('./src'))
from dota_db import DotaDB
from basic_logger import setup_logger

setup_logger(logfile_path='logs/fetch_teams.log')
db = DotaDB()

def main():
    query = '''
        SELECT DISTINCT "radiantTeamId" 
        FROM match_details 
        UNION 
        SELECT DISTINCT "direTeamId" 
        FROM match_details;
    '''
    team_ids = [tid[0] for tid in db.select(query)]
    query = '''
        query($teamIds: [Int]!) {
            teams(teamIds: $teamIds) {
                id
                name
                tag
                dateCreated
                isPro
                isLocked
                countryCode
                countryName
                url
                logo
                baseLogo
                bannerLogo
                leagues {
                    id
                }
            }
        }
    '''
    saved_ids = [res[0] for res in db.select('SELECT id FROM team_details')]
    for tid in saved_ids:
        if tid in team_ids:
            team_ids.remove(tid)
    with httpx.Client(headers=db.stratz_headers) as client:
        storage = []
        team_leagues = []
        for i in range(0, len(team_ids), 5):
            if i == (len(team_ids) // 5 * 5):
                variables = {'teamIds': team_ids[i:]}
            else:
                variables = {'teamIds': team_ids[i:(i+5)]}
            result = db.fetch_stratz(client, query, variables)['data']['teams']
            for team in result:
                storage.append(team)
                team_leagues.extend((team['id'], league['id']) for league in team['leagues'])
            if i == 0:
                df_team = pd.DataFrame(storage).drop('leagues', axis=1)
                db.create_table_from_df(df_team, 'team_details')
            if i != 0 and i % 500 == 0:
                flush_storage(storage, team_leagues)
                storage.clear()
                team_leagues.clear()
        flush_storage(storage, team_leagues)

def flush_storage(storage, team_leagues):
    df_tl = pd.DataFrame(team_leagues, columns=['team_id', 'league_id'])
    db.insert_df_into_table(df_tl, 'team_leagues')
    df_team = pd.DataFrame(storage).drop('leagues', axis=1)
    db.insert_df_into_table(df_team, 'team_details')
            
if __name__ == '__main__':
    main()