import pandas as pd
import numpy as np
import pyarrow.parquet as pq
from src.database import DatabaseManager
from src.analytics import PlayerHistoryManager, StateManager, RatingSystem, MatchFeatureExtractor
import joblib

raw_alpha = input('Enter ALPHA (default 20): ')
ALPHA = int(raw_alpha) if raw_alpha else 20

raw_window = input('Enter ROLLING_MAJOR_WINDOW (default 3): ')
WINDOW_SIZE = int(raw_window) if raw_window else 3 

def process_matches(df_raw, feature_extractor: MatchFeatureExtractor, db: DatabaseManager):
    training_data = []
    for index, match in df_raw.iterrows():
        m_id = match['match_id']
        rad_won = match['rad_won']
        rad_data = match['rad_heroes']  
        dire_data = match['dire_heroes']
        
        major_patch = match['major_patch_id']
        sub_patch = match['patch']

        rad_heroes = [h for h, a in rad_data if h != 0]
        rad_player_ids = [a for h, a in rad_data]
        dire_heroes = [h for h, a in dire_data if h != 0]
        dire_player_ids = [a for h, a in dire_data]

        features = feature_extractor.build_draft_feature_dict(
            rad_heroes, 
            dire_heroes, 
            rad_player_ids,
            dire_player_ids,
            major_patch,
            sub_patch 
        )
        features['match_id'] = m_id
        training_data.append(features)

        sm.update({'patch': sub_patch, 'major_patch_id': major_patch, 
                   'rad_heroes': rad_heroes, 'dire_heroes': dire_heroes, 'rad_won': rad_won})
                   
        for hero_id, account_id in rad_data:
            pm.update(account_id, hero_id, rad_won, major_patch, sub_patch)
        for hero_id, account_id in dire_data:
            pm.update(account_id, hero_id, not rad_won, major_patch, sub_patch)
                   
        if index % 5000 == 0 and index > 0:
            print(f'{index} matches processed')
            
    print('Saving state and player history manager data to the DB')
    sm.save(db)
    pm.save(db)
    print('Constructing and returning DataFrame')
    return pd.DataFrame(training_data)

def aggregate_match(group):
    rad_mask = group['isRadiant']
    dire_mask = ~group['isRadiant']
    
    return pd.Series({
        'patch': group['patch'].iloc[0],
        'major_patch_id': group['major_patch_id'].iloc[0],
        'rad_won': group['rad_won'].iloc[0],
        
        'rad_heroes': list(zip(group[rad_mask]['heroId'], group[rad_mask]['steamAccountId'])),
        'dire_heroes': list(zip(group[dire_mask]['heroId'], group[dire_mask]['steamAccountId']))
    })

if __name__ == '__main__':
    db = DatabaseManager()
    query = """
    SELECT 
        md.id AS match_id, 
        md."gameVersionId" AS patch, 
        p.opendota_patch_id AS major_patch_id,
        md."didRadiantWin" AS rad_won,
        mp."heroId", 
        mp."steamAccountId",
        mp."isRadiant"
    FROM match_details md
    JOIN match_players mp ON md.id = mp.match_id
    JOIN patches p ON md."gameVersionId" = p.id
    ORDER BY md."startDateTimeHuman" ASC
    """
    print('Fetching match details...')
    df_matches_sorted = db.select_to_df(query)
    print('Aggregating match data...')
    df_raw = df_matches_sorted.groupby('match_id').apply(aggregate_match).reset_index()
    print('Starting processing matches...')
    sm = StateManager(window_size=WINDOW_SIZE)
    pm = PlayerHistoryManager()
    db = DatabaseManager()
    rs = RatingSystem(db_manager=db)
    feature_extractor = MatchFeatureExtractor(rs, sm, pm)
    df_final = process_matches(df_raw, feature_extractor=feature_extractor, db=db)
    
    output_filename = f'data/alpha_{ALPHA}_window_{WINDOW_SIZE}.parquet'
    print(f'Saving to {output_filename}...')
    df_final.to_parquet(output_filename)
    joblib.dump(sm, 'data/state_manager.joblib')
    joblib.dump(pm, 'data/player_history_manager.joblib')
    print(f'Saved status of State and Player History Manager')