from collections import defaultdict, deque
import numpy as np

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
                    
            self.history_queue.append(outgoing_snapshot)
            
            if len(self.history_queue) > self.WINDOW_SIZE:
                print("Window limit reached. Forgetting oldest major patch data.")
                oldest_snapshot = self.history_queue.popleft()
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