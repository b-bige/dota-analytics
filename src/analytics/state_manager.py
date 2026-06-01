from collections import defaultdict, deque
import numpy as np
import pandas as pd
from src.database import DatabaseManager

class StateManager:
    @staticmethod
    def _default_stats():
        return [0, 0]
    
    def __init__(self, window_size=3, alpha=20):
        self.ALPHA = alpha
        self.WINDOW_SIZE = window_size
        self.current_sub_patch = None
        self.current_major_patch = None
        
        self.sub_patch_stats = self.new_stats_dict()
        self.major_patch_stats = self.new_stats_dict()
        
        self.recent_history_stats = self.new_stats_dict()
        self.history_queue = deque() 

    def new_stats_dict(self):
        return {
            "hero": defaultdict(self._default_stats), 
            "syn": defaultdict(self._default_stats), 
            "cnt": defaultdict(self._default_stats)
        }

    def _get_wr(self, wins, games, prior_wr=0.5):
        return (wins + (self.ALPHA * prior_wr)) / (games + self.ALPHA)

    def get_feature_score(self, key, stat_type):
        hist_w, hist_g = self.recent_history_stats[stat_type][key]
        major_w, major_g = self.major_patch_stats[stat_type][key]
        sub_w, sub_g = self.sub_patch_stats[stat_type][key]

        hist_wr = hist_w / hist_g if hist_g > 0 else 0.5

        major_wr = self._get_wr(major_w, major_g, hist_wr)

        return self._get_wr(sub_w, sub_g, major_wr)

    def update(self, match_data):
        sub_patch = match_data['patch']
        major_patch = match_data['major_patch_id']

        if self.current_major_patch is None:
            self.current_major_patch = major_patch
            self.current_sub_patch = sub_patch

        if major_patch != self.current_major_patch:
            print(f"\n--- New Major Patch: {major_patch} ---")
            print("Archiving old meta into recent history window...")
            
            outgoing_snapshot = self.new_stats_dict()
            for s_type in ["hero", "syn", "cnt"]:
                for k, (w, g) in self.major_patch_stats[s_type].items():
                    outgoing_snapshot[s_type][k] = [w, g]
                    self.recent_history_stats[s_type][k][0] += w
                    self.recent_history_stats[s_type][k][1] += g
                    
            self.history_queue.append((self.current_major_patch, outgoing_snapshot))
            
            if len(self.history_queue) > self.WINDOW_SIZE:
                print("Window limit reached. Forgetting oldest major patch data.")
                oldest_patch, oldest_snapshot = self.history_queue.popleft()
                for s_type in ["hero", "syn", "cnt"]:
                    for k, (w, g) in oldest_snapshot[s_type].items():
                        self.recent_history_stats[s_type][k][0] -= w
                        self.recent_history_stats[s_type][k][1] -= g

            self.major_patch_stats = self.new_stats_dict()
            self.sub_patch_stats = self.new_stats_dict()
            self.current_major_patch = major_patch
            self.current_sub_patch = sub_patch

        elif sub_patch != self.current_sub_patch:
            print(f"Sub-Patch {sub_patch} detected. Clearing sub-patch stats (Major stats retained).")
            self.sub_patch_stats = self.new_stats_dict()
            self.current_sub_patch = sub_patch

        rad_heroes = match_data['rad_heroes']
        dire_heroes = match_data['dire_heroes']
        rad_won = match_data['rad_won']

        for is_rad, heroes, opponents in [(True, rad_heroes, dire_heroes), (False, dire_heroes, rad_heroes)]:
            won = (is_rad == rad_won)
            for i, h1 in enumerate(heroes):
                for stats_dict in [self.sub_patch_stats, self.major_patch_stats]:
                    stats_dict["hero"][h1][0] += int(won)
                    stats_dict["hero"][h1][1] += 1

                for h2 in heroes[i+1:]:
                    pair = tuple(sorted((h1, h2)))
                    for stats_dict in [self.sub_patch_stats, self.major_patch_stats]:
                        stats_dict["syn"][pair][0] += int(won)
                        stats_dict["syn"][pair][1] += 1
                
                for e_id in opponents:
                    pair = (h1, e_id)
                    for stats_dict in [self.sub_patch_stats, self.major_patch_stats]:
                        stats_dict["cnt"][pair][0] += int(won)
                        stats_dict["cnt"][pair][1] += 1
    
    def save(self, db: DatabaseManager) -> None:
        """
        Saves the state of the class to the respective database tables. To be called only when the feature engineering
        changes and the features are re-calculated for the entire dataset.
        """
        db.execute('DELETE FROM state_manager_meta')
        db.execute(
            'INSERT INTO state_manager_meta (current_sub_patch, current_major_patch) VALUES (:sub, :major)',
            params={'sub': self.current_sub_patch, 'major': self.current_major_patch}
        )
        stats_rows = []
        for scope, stats in [('sub_patch', self.sub_patch_stats), ('major_patch', self.major_patch_stats)]:
            for stat_type in ['hero', 'syn', 'cnt']:
                for key, (wins, games) in stats[stat_type].items():
                    if isinstance(key, tuple):
                        key_a, key_b = key
                    else:
                        key_a, key_b = key, -1
                    stats_rows.append((scope, stat_type, int(key_a), int(key_b), wins, games))

        db.execute('DELETE FROM state_manager_stats')
        if stats_rows:
            db.insert_df_into_table(
                pd.DataFrame(stats_rows, columns=['scope', 'stat_type', 'key_a', 'key_b', 'wins', 'games']),
                'state_manager_stats',
                conflict_cols=['scope', 'stat_type', 'key_a', 'key_b']
            )

        hist_rows = []
        for stat_type in ['hero', 'syn', 'cnt']:
            for key, (wins, games) in self.recent_history_stats[stat_type].items():
                if isinstance(key, tuple):
                    key_a, key_b = key
                else:
                    key_a, key_b = key, -1
                hist_rows.append((stat_type, int(key_a), int(key_b), wins, games))

        db.execute('DELETE FROM state_manager_history')
        if hist_rows:
            db.insert_df_into_table(
                pd.DataFrame(hist_rows, columns=['stat_type', 'key_a', 'key_b', 'wins', 'games']),
                'state_manager_history',
                conflict_cols=['stat_type', 'key_a', 'key_b']
            )

        queue_rows = []
        for pos, (major_patch, snapshot) in enumerate(self.history_queue):
            for stat_type in ['hero', 'syn', 'cnt']:
                for key, (wins, games) in snapshot[stat_type].items():
                    key_a, key_b = key if isinstance(key, tuple) else (key, -1)
                    
                    queue_rows.append((
                        pos, major_patch, stat_type, 
                        int(key_a), int(key_b), 
                        wins, games
                    ))

        db.execute('DELETE FROM state_manager_queue')
        if queue_rows:
            db.insert_df_into_table(
                pd.DataFrame(queue_rows, columns=['queue_position', 'major_patch', 'stat_type', 'key_a', 'key_b', 'wins', 'games']),
                'state_manager_queue',
                conflict_cols=['queue_position', 'stat_type', 'key_a', 'key_b']
            )