import pandas as pd
import numpy as np
from collections import defaultdict
import pyarrow.parquet as pq
from src.database import DatabaseManager

ALPHA = 20  
MIN_PATCH_GAMES = 50 

class StateManager:
    def __init__(self):
        self.current_patch = None
        self.stats = {
            "global": {"hero": defaultdict(lambda: [0, 0]), "syn": defaultdict(lambda: [0, 0]), "cnt": defaultdict(lambda: [0, 0])},
            "previous": {"hero": defaultdict(lambda: [0, 0]), "syn": defaultdict(lambda: [0, 0]), "cnt": defaultdict(lambda: [0, 0])},
            "current": {"hero": defaultdict(lambda: [0, 0]), "syn": defaultdict(lambda: [0, 0]), "cnt": defaultdict(lambda: [0, 0])}
        }

    def _get_wr(self, wins, games, prior_wr=0.5):
        return (wins + (ALPHA * prior_wr)) / (games + ALPHA)

    def get_feature_score(self, key, stat_type):
        curr_w, curr_g = self.stats["current"][stat_type][key]
        prev_w, prev_g = self.stats["previous"][stat_type][key]
        glob_w, glob_g = self.stats["global"][stat_type][key]

        global_wr = glob_w / glob_g if glob_g > 0 else 0.5

        prev_wr = prev_w / prev_g if prev_g > 0 else global_wr

        effective_prior = prev_wr if curr_g < MIN_PATCH_GAMES else global_wr
        
        return self._get_wr(curr_w, curr_g, effective_prior)

    def update(self, match_data):
        if match_data['patch'] != self.current_patch:
            print(f"New Patch detected: {match_data['patch']}. Archiving old data...")
            self.stats["previous"] = {k: v.copy() for k, v in self.stats["current"].items()}
            for k in self.stats["current"]: self.stats["current"][k].clear()
            self.current_patch = match_data['patch']

        rad_heroes = match_data['rad_heroes']
        dire_heroes = match_data['dire_heroes']
        rad_won = match_data['rad_won']

        for is_rad, heroes, opponents in [(True, rad_heroes, dire_heroes), (False, dire_heroes, rad_heroes)]:
            won = (is_rad == rad_won)
            for i, h1 in enumerate(heroes):
                for scope in ["global", "current"]:
                    self.stats[scope]["hero"][h1][0] += int(won)
                    self.stats[scope]["hero"][h1][1] += 1
                
                for h2 in heroes[i+1:]:
                    pair = tuple(sorted((h1, h2)))
                    for scope in ["global", "current"]:
                        self.stats[scope]["syn"][pair][0] += int(won)
                        self.stats[scope]["syn"][pair][1] += 1
                
                for e_id in opponents:
                    pair = (h1, e_id)
                    for scope in ["global", "current"]:
                        self.stats[scope]["cnt"][pair][0] += int(won)
                        self.stats[scope]["cnt"][pair][1] += 1

def process_matches(df_raw, weights=None):
    sm = StateManager()
    weights = weights or [0.40, 0.35, 0.25]
    training_data = []

    print("Starting simulation...")
    for _, match in df_raw.iterrows():
        m_id = match['match_id']
        rad_heroes = match['rad_heroes']
        dire_heroes = match['dire_heroes']

        features = {}
        for side, heroes, enemies in [('rad', rad_heroes, dire_heroes), ('dire', dire_heroes, rad_heroes)]:
            h_wrs = [sm.get_feature_score(h, "hero") for h in heroes]
            features[f'{side}_hero_wr'] = np.mean(h_wrs)
            
            syns = [sm.get_feature_score(tuple(sorted((h1, h2))), "syn") for i, h1 in enumerate(heroes) for h2 in heroes[i+1:]]
            features[f'{side}_syn_wr'] = np.mean(syns) if syns else 0.5
            
            cnts = [sm.get_feature_score((h, e), "cnt") for h in heroes for e in enemies]
            features[f'{side}_cnt_wr'] = np.mean(cnts) if cnts else 0.5

        training_data.append({
            'match_id': m_id,
            'draft_diff': (weights[0] * features['rad_hero_wr'] + weights[1] * features['rad_syn_wr'] + weights[2] * features['rad_cnt_wr']) - 
                          (weights[0] * features['dire_hero_wr'] + weights[1] * features['dire_syn_wr'] + weights[2] * features['dire_cnt_wr']),
            'label': 1 if match['rad_won'] else 0
        })

        sm.update(match)
        if _ % 1000 == 0:
            print(f'{_} matches processed out of {len(df_raw)}')
    print('Constructing and returning DataFrame...')
    return pd.DataFrame(training_data)

def aggregate_match(group):
    return pd.Series({
        'patch': group['patch'].iloc[0],
        'rad_won': group['rad_won'].iloc[0],
        'rad_heroes': group[group['isRadiant']]['heroId'].tolist(),
        'dire_heroes': group[~group['isRadiant']]['heroId'].tolist()
    })

if __name__ == '__main__':
    #TODO: Save the radiant draft score and dire draft scores as well
    db = DatabaseManager()
    query = """
    SELECT 
        md.id AS match_id, 
        md."gameVersionId" AS patch, 
        md."didRadiantWin" AS rad_won,
        mp."heroId", 
        mp."isRadiant"
    FROM match_details md
    JOIN match_players mp ON md.id = mp.match_id
    ORDER BY md."startDateTimeHuman" ASC
    """
    df_matches_sorted = db.select_to_df(query)
    df_raw = df_matches_sorted.groupby('match_id').apply(aggregate_match).reset_index()
    df_final = process_matches(df_raw)
    print('Saving to parquet...')
    df_final.to_parquet('data/training_set_v1.parquet')