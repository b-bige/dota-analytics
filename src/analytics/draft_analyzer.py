import logging
import numpy as np
from database.dota_db import DotaDB

class DraftAnalyzer:
    def __init__(self, db: DotaDB):
        self.db = db
        self.load_draft_cache()

    def load_draft_cache(self):
        """
        Precompute hero winrates, synergy and counter tables into memory.
        """
        #TODO: per-patch stats for everything
        logging.info("Loading draft cache...")
        hero_wr = self.db.select_to_df('''
            SELECT 
                mp."heroId"                         AS hero_id,
                md."gameVersionId",
                AVG(CAST(mp."isVictory" AS INT))    AS winrate,
                COUNT(*)                            AS games
            FROM match_players mp
            JOIN match_details md ON md.id = mp.match_id
            GROUP BY mp."heroId", md."gameVersionId"
            HAVING COUNT(*) >= 20
        ''', columns=['hero_id', 'patch', 'winrate', 'games'])
        hero_wr['winrate'] = hero_wr['winrate'].astype(float)

        # Hero synergy — same team pair win rates
        synergy = self.db.select_to_df('SELECT * FROM hero_synergy_stats', columns=['hero1', 'hero2', 'winrate', 'games'])
        synergy['winrate'] = synergy['winrate'].astype(float)

        # Hero counters — opposite team pair win rates
        counters = self.db.select_to_df('SELECT * FROM hero_counter_stats', columns=['hero_id', 'enemy_id', 'winrate', 'games'])
        counters['winrate'] = counters['winrate'].astype(float)

        self._hero_wr_cache = {
            (row.hero_id, row.patch): row.winrate
            for row in hero_wr.itertuples()
        }
        self._hero_wr_by_hero = {
            hero_id: grp['winrate'].mean()
            for hero_id, grp in hero_wr.groupby('hero_id')
        }
        self._synergy_cache = {
            (row.hero1, row.hero2): row.winrate
            for row in synergy.itertuples()
        }
        self._counter_cache = {
            (row.hero_id, row.enemy_id): row.winrate
            for row in counters.itertuples()
        }

        logging.info(f"Draft cache loaded — "
                f"{len(self._hero_wr_cache)} hero/patch entries, "
                f"{len(self._synergy_cache)} synergy pairs, "
                f"{len(self._counter_cache)} counter matchups.")
        
    def _hero_winrate(self, hero_id: int, patch: int) -> float:
        """Patch-specific winrate with fallback to overall hero winrate."""
        return (
            self._hero_wr_cache.get((hero_id, patch)) or
            self._hero_wr_by_hero.get(hero_id) or
            0.50
        )

    def _synergy_score(self, hero1: int, hero2: int) -> float | None:
        key = (min(hero1, hero2), max(hero1, hero2))
        return self._synergy_cache.get(key)

    def _counter_score(self, hero_id: int, enemy_id: int) -> float | None:
        return self._counter_cache.get((hero_id, enemy_id))

    def compute_draft_strength(
        self,
        team_heroes: list[int],
        enemy_heroes: list[int],
        patch: int,
        weights: tuple[float, float, float] = (0.40, 0.35, 0.25)
    ) -> float:
        """
        Compute draft strength score for a team.
        Args:
            team_heroes:  list of hero IDs for this team (max 5)
            enemy_heroes: list of hero IDs for the enemy team (max 5)
            patch:        current patch as int
            weights:      (hero_wr, synergy, counter) weights — must sum to 1.0
        Returns:
            float 0-1, higher = stronger draft
        """
        w_wr, w_syn, w_ctr = weights

        hero_wr_score = np.mean([
            self._hero_winrate(h, patch)
            for h in team_heroes
        ])

        synergy_scores = [
            self._synergy_score(h1, h2)
            for i, h1 in enumerate(team_heroes)
            for h2 in team_heroes[i+1:]
        ]
        synergy_scores = [s for s in synergy_scores if s is not None]
        synergy_score = np.mean(synergy_scores) if synergy_scores else 0.50

        counter_scores = [
            self._counter_score(h, e)
            for h in team_heroes
            for e in enemy_heroes
        ]
        counter_scores = [c for c in counter_scores if c is not None]
        counter_score = np.mean(counter_scores) if counter_scores else 0.50

        return (
            w_wr  * hero_wr_score +
            w_syn * synergy_score +
            w_ctr * counter_score
        )
    
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