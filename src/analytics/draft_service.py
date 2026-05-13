import logging
import numpy as np
import pandas as pd
import os
from diskcache import Cache
from cachetools import TTLCache, cached
from src.database import DatabaseManager 

class DraftService:
    def __init__(self, db: DatabaseManager, cache_dir='cache/draft_stats', refresh_interval: int = 3600):
        self.db = db
        self._refresh_interval = refresh_interval
        os.makedirs(cache_dir, exist_ok=True)
        self._cache = Cache(cache_dir, timeout=refresh_interval)
        self._global_winrate = 0.50

    def _apply_smoothing(self, wins: float, total: int, prior_weight: int = 5) -> float:
        return (wins + (prior_weight * self._global_winrate)) / (total + prior_weight)
    
    def _get_cached_stat(self, key, fetch_func):
        val = self._cache.get(key)
        if val is None:
            val = fetch_func()
            self._cache.set(key, val, expire=self._refresh_interval)
            return val
        return val
    
    def _get_hero_stats(self):
        return self._get_cached_stat('hero_stats', self._fetch_hero_stats)

    def _get_synergy_stats(self):
        return self._get_cached_stat('synergy_stats', self._fetch_synergy_stats)

    def _get_counter_stats(self):
        return self._get_cached_stat('counter_stats', self._fetch_counter_stats)
    
    def _fetch_hero_stats(self) -> dict[tuple[int, int], float]:
        """Fetch individual hero winrates and apply Bayesian smoothing."""
        query = "SELECT hero_id, patch, wins, games FROM hero_patch_stats"
        df = self.db.select_to_df(query)
        
        df['wins'] = df['wins'].astype(int)
        df['games'] = df['games'].astype(int)
        
        df['smoothed_wr'] = df.apply(
            lambda x: self._apply_smoothing(x['wins'], x['games']), axis=1
        )
        return df.set_index(['hero_id', 'patch'])['smoothed_wr'].to_dict()
    
    def _fetch_synergy_stats(self) -> dict[tuple[int, int, int], float]:
        """Fetch pairwise synergy metrics and apply Bayesian smoothing."""
        query = "SELECT patch, hero_a, hero_b, wins, games FROM hero_synergy_stats"
        df = self.db.select_to_df(query)
        
        df['wins'] = df['wins'].astype(int)
        df['games'] = df['games'].astype(int)
        
        df['smoothed_score'] = df.apply(
            lambda x: self._apply_smoothing(x['wins'], x['games']), axis=1
        )
        return df.set_index(['patch', 'hero_a', 'hero_b'])['smoothed_score'].to_dict()
    
    def _fetch_counter_stats(self) -> dict[tuple[int, int, int], float]:
        """Fetch counter matchup metrics and apply Bayesian smoothing"""
        query = "SELECT patch, hero_id, enemy_id, wins, games FROM hero_counter_stats"
        df = self.db.select_to_df(query)
        
        df['wins'] = df['wins'].astype(int)
        df['games'] = df['games'].astype(int)
        
        df['smoothed_score'] = df.apply(
            lambda x: self._apply_smoothing(x['wins'], x['games']), axis=1
        )
        return df.set_index(['patch', 'hero_id', 'enemy_id'])['smoothed_score'].to_dict()
    
    def compute_draft_strength(self, team_heroes, enemy_heroes, patch, weights=None, stats_maps=None):
        weights = weights or [0.40, 0.35, 0.25]

        if stats_maps:
            winrate_map, synergy_map, counter_map = stats_maps
        else:
            winrate_map = self._get_hero_stats()
            synergy_map = self._get_synergy_stats()
            counter_map = self._get_counter_stats()

        hero_scores = [winrate_map.get((h, patch), winrate_map.get((h, 0), 0.5)) for h in team_heroes]
        wr_score = sum(hero_scores) / len(hero_scores) if hero_scores else 0.5

        syn_total = 0
        syn_count = 0
        for i, h1 in enumerate(team_heroes):
            for h2 in team_heroes[i+1:]:
                h_low, h_high = (h1, h2) if h1 < h2 else (h2, h1)
                score = synergy_map.get((patch, h_low, h_high), synergy_map.get((0, h_low, h_high), 0.5))
                syn_total += score
                syn_count += 1
        synergy_score = syn_total / syn_count if syn_count > 0 else 0.5

        cnt_total = 0
        for h in team_heroes:
            for e in enemy_heroes:
                cnt_total += counter_map.get((patch, h, e), counter_map.get((0, h, e), 0.5))
        counter_score = cnt_total / 25

        return (weights[0] * wr_score) + (weights[1] * synergy_score) + (weights[2] * counter_score)
    
    def _calculate_synergy(self, team_heroes: list[int], patch: int) -> float:
        stats = self._get_synergy_stats()
        scores = []
        
        for i, h1 in enumerate(team_heroes):
            for h2 in team_heroes[i+1:]:
                key_a = (patch, min(h1, h2), max(h1, h2))
                key_b = (0, min(h1, h2), max(h1, h2))
                
                scores.append(stats.get(key_a, stats.get(key_b, 0.50)))
                
        return float(np.mean(scores)) if scores else 0.50

    def _calculate_counters(self, team_heroes: list[int], enemy_heroes: list[int], patch: int) -> float:
        stats = self._get_counter_stats()
        scores = []
        
        for h in team_heroes:
            for e in enemy_heroes:
                key_a = (patch, h, e)
                key_b = (0, h, e)
                
                scores.append(stats.get(key_a, stats.get(key_b, 0.50)))
                
        return float(np.mean(scores)) if scores else 0.50
    
    def draft_is_complete(self, match: dict) -> bool:
        """
        Checks if a match dict returned by OpenDota Live API 
        has the draft phase concluded. 
        """
        players = match.get('players', [])
        if len(players) != 10:
            return False
        
        heroes_assigned = all(p.get('hero_id', 0) != 0 for p in players)
        if not heroes_assigned:
            return False
        
        radiant = [p for p in players if p.get('team') == 0]
        dire    = [p for p in players if p.get('team') == 1]
        
        return len(radiant) == 5 and len(dire) == 5

    def get_draft(self, match: dict, live=True) -> tuple[list[int], list[int]]:
        """
        Extract team drafts from match dict returned by OpenDota Live API
        Returns a tuple of 2 lists containing the hero IDs for each team.
        """
        players = match.get('players', [])
        if live:
            radiant_heroes = [p['hero_id'] for p in players if p.get('team') == 0]
            dire_heroes    = [p['hero_id'] for p in players if p.get('team') == 1]
        else:
            radiant_heroes = [p['hero_id'] for p in players if p.get('isRadiant') == True]
            dire_heroes    = [p['hero_id'] for p in players if p.get('isRadiant') == False]
        return radiant_heroes, dire_heroes