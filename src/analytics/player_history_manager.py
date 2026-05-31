from collections import defaultdict, deque
import numpy as np

class PlayerHistoryManager:
    @staticmethod
    def _stats_factory():
        return [0, 0]

    @staticmethod
    def _hero_stats_factory():
        return defaultdict(PlayerHistoryManager._stats_factory)

    @staticmethod
    def _player_stats_factory():
        return defaultdict(PlayerHistoryManager._hero_stats_factory)
        
    @staticmethod
    def _history_queue():
        return defaultdict(deque)

    def __init__(self, window_size=3, alpha=5):
        self.ALPHA = alpha
        self.WINDOW_SIZE = window_size
        self.current_sub_patch = None
        self.current_major_patch = None
        self.sub_patch_stats  = defaultdict(self._player_stats_factory)
        self.major_patch_stats = defaultdict(self._player_stats_factory)
        self.recent_history_stats = defaultdict(self._hero_stats_factory)
        self.history_queue = defaultdict(self._history_queue)

    def get_player_hero_wr(self, account_id, hero_id, global_hero_wr):
        if not account_id or account_id == 0:
            return global_hero_wr

        hist_w, hist_g = self.recent_history_stats[account_id][hero_id]
        hist_wr = hist_w / hist_g if hist_g > 0 else global_hero_wr 

        maj_w, maj_g = self.major_patch_stats[account_id][hero_id].get(self.current_major_patch, [0, 0])
        major_wr = (maj_w + self.ALPHA * hist_wr) / (maj_g + self.ALPHA)

        sub_w, sub_g = self.sub_patch_stats[account_id][hero_id].get(self.current_sub_patch, [0, 0])
        return (sub_w + self.ALPHA * major_wr) / (sub_g + self.ALPHA)    
    
    def get_player_hero_wr(self, account_id, hero_id, global_hero_wr, current_major, current_sub):
        if not account_id or account_id == 0:
            return global_hero_wr

        hist_w, hist_g = self.recent_history_stats[account_id][hero_id]
        hist_wr = hist_w / hist_g if hist_g > 0 else global_hero_wr

        maj_w, maj_g = self.major_patch_stats[account_id][hero_id].get(current_major, [0, 0])
        major_wr = (maj_w + self.ALPHA * hist_wr) / (maj_g + self.ALPHA)

        sub_w, sub_g = self.sub_patch_stats[account_id][hero_id].get(current_sub, [0, 0])
        return (sub_w + self.ALPHA * major_wr) / (sub_g + self.ALPHA)    
    
    def update(self, account_id, hero_id, won, major_patch, sub_patch):
        if not account_id or account_id == 0:
            return

        if self.current_major_patch is None:
            self.current_major_patch = major_patch
            self.current_sub_patch = sub_patch

        if major_patch != self.current_major_patch:
            for acc in self.major_patch_stats:
                for h in self.major_patch_stats[acc]:
                    w, g = self.major_patch_stats[acc][h].get(self.current_major_patch, [0, 0])
                    if g == 0:
                        continue
                    self.recent_history_stats[acc][h][0] += w
                    self.recent_history_stats[acc][h][1] += g
                    self.history_queue[acc][h].append((self.current_major_patch, [w, g]))
                    
                    if len(self.history_queue[acc][h]) > self.WINDOW_SIZE:
                        _, (old_w, old_g) = self.history_queue[acc][h].popleft()
                        self.recent_history_stats[acc][h][0] -= old_w
                        self.recent_history_stats[acc][h][1] -= old_g

            self.current_major_patch = major_patch
            self.current_sub_patch = sub_patch

        elif sub_patch != self.current_sub_patch:
            self.current_sub_patch = sub_patch

        self.major_patch_stats[account_id][hero_id][major_patch][0] += int(won)
        self.major_patch_stats[account_id][hero_id][major_patch][1] += 1
        self.sub_patch_stats[account_id][hero_id][sub_patch][0] += int(won)
        self.sub_patch_stats[account_id][hero_id][sub_patch][1] += 1