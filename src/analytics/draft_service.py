import logging
import numpy as np
import pandas as pd
from cachetools import TTLCache, cached
from src.database import DatabaseManager 

class DraftService:
    def __init__(self, db: DatabaseManager, refresh_interval: int = 3600):
        self.db = db
        self._refresh_interval = refresh_interval
        self._hero_stats = TTLCache(maxsize=1, ttl=refresh_interval)
        self._synergy_stats = TTLCache(maxsize=1, ttl=refresh_interval)
        self._counter_stats = TTLCache(maxsize=1, ttl=refresh_interval)
        
        self._global_winrate = 0.50

    def _apply_smoothing(self, wins: float, total: int, prior_weight: int = 5) -> float:
        return (wins + (prior_weight * self._global_winrate)) / (total + prior_weight)
    
    def _get_hero_stats(self) -> dict[tuple[int, int], float]:
        """Fetch individual hero winrates from the materialized view and apply Bayesian smoothing."""
        if 'data' not in self._hero_stats:
            query = "SELECT hero_id, patch, wins, games FROM hero_patch_stats"
            df = self.db.select_to_df(query)
            
            df['wins'] = df['wins'].astype(int)
            df['games'] = df['games'].astype(int)
            
            df['smoothed_wr'] = df.apply(
                lambda x: self._apply_smoothing(x['wins'], x['games']), axis=1
            )
            self._hero_stats['data'] = df.set_index(['hero_id', 'patch'])['smoothed_wr'].to_dict()
            
        return self._hero_stats['data']
    
    def _get_synergy_stats(self) -> dict[tuple[int, int, int], float]:
        """Fetch and smooth pairwise synergy metrics."""
        if 'data' not in self._synergy_stats:
            query = "SELECT patch, hero_a, hero_b, wins, games FROM hero_synergy_stats"
            df = self.db.select_to_df(query)
            
            df['wins'] = df['wins'].astype(int)
            df['games'] = df['games'].astype(int)
            
            df['smoothed_score'] = df.apply(
                lambda x: self._apply_smoothing(x['wins'], x['games']), axis=1
            )
            self._synergy_stats['data'] = df.set_index(['patch', 'hero_a', 'hero_b'])['smoothed_score'].to_dict()
            
        return self._synergy_stats['data']
    
    def _get_counter_stats(self) -> dict[tuple[int, int, int], float]:
        """Fetch and smooth counter matchup metrics."""
        if 'data' not in self._counter_stats:
            query = "SELECT patch, hero_id, enemy_id, wins, games FROM hero_counter_stats"
            df = self.db.select_to_df(query)
            
            df['wins'] = df['wins'].astype(int)
            df['games'] = df['games'].astype(int)
            
            df['smoothed_score'] = df.apply(
                lambda x: self._apply_smoothing(x['wins'], x['games']), axis=1
            )
            self._counter_stats['data'] = df.set_index(['patch', 'hero_id', 'enemy_id'])['smoothed_score'].to_dict()
            
        return self._counter_stats['data']
    
    def compute_draft_strength(
        self,
        team_heroes: list[int],
        enemy_heroes: list[int],
        patch: int,
        weights: dict[str, float] = None
    ) -> float:
        """Computes a draft score by evaluating individual hero winrates, synergy, and counter-picks."""
        weights = weights or {"winrate": 0.40, "synergy": 0.35, "counter": 0.25}
        
        stats = self._get_hero_stats()
        hero_scores = [
            stats.get((h, patch), stats.get((h, 0), 0.50)) 
            for h in team_heroes
        ]
        wr_score = np.mean(hero_scores) if hero_scores else 0.50
        synergy_score = self._calculate_synergy(team_heroes, patch)
        counter_score = self._calculate_counters(team_heroes, enemy_heroes, patch)

        return float(
            weights["winrate"] * wr_score + 
            weights["synergy"] * synergy_score + 
            weights["counter"] * counter_score
        )
    
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