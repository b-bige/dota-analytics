import logging
import pandas as pd
import numpy as np
from cachetools import LRUCache
from openskill.models import PlackettLuce, PlackettLuceRating
from src.database import DatabaseManager
class RatingSystem:
    def __init__(self, db_manager: DatabaseManager, model_tau: float=0.5):
        self.db = db_manager
        self.model = PlackettLuce(model_tau)
        self._rating_cache = LRUCache(maxsize=50000)

    def _create_rating_obj(self, mu: float, sigma: float) -> PlackettLuceRating:
        """Helper to reconstruct OpenSkill objects."""
        return self.model.rating(mu=mu, sigma=sigma)
    
    def get_ratings(self, account_ids: list[int]) -> dict[int, PlackettLuceRating]:
        """
        Fetches the player ratings based on their account IDs. 
        Updates cache when an account's ID is not present.
        """
        results = {aid: self._rating_cache[aid] for aid in account_ids if aid in self._rating_cache}
        missing_ids = list(set(account_ids) - set(results.keys()))

        if missing_ids:
            query = "SELECT account_id, mu, sigma FROM current_player_ratings WHERE account_id = ANY(:ids)"
            rows = self.db.select(query, {"ids": missing_ids})
            
            for aid, mu, sigma in rows:
                rating = self._create_rating_obj(float(mu), float(sigma))
                self._rating_cache[aid] = rating
                results[aid] = rating
                
            for aid in set(missing_ids) - set(results.keys()):
                new_rating = self.model.rating()
                self._rating_cache[aid] = new_rating
                results[aid] = new_rating
                
        return results
    
    def calculate_rating_features(self, rad_ratings: list[PlackettLuceRating], dire_ratings: list[PlackettLuceRating]) -> dict:
        """
        Returns a dictionary of rating-related features derived from two teams' 
        list of PlackettLuceRating objects required for making predictions.
        """
        rad_mus = np.array([r.mu for r in rad_ratings])
        dire_mus = np.array([r.mu for r in dire_ratings])

        mu_rad = np.mean(rad_mus)
        mu_dire = np.mean(dire_mus)
        mu_diff = mu_rad - mu_dire
        max_mu_rad = np.max(rad_mus)
        max_mu_dire = np.max(dire_mus)
        max_mu_diff = max_mu_rad - max_mu_dire
        std_mu_rad = np.std(rad_mus)
        std_mu_dire = np.std(dire_mus)
        std_diff = std_mu_rad - std_mu_dire
        sigma_total_rad = np.sum(np.array([r.sigma for r in rad_ratings]))
        sigma_total_dire = np.sum(np.array([r.sigma for r in dire_ratings]))
        sigma_total_diff = sigma_total_rad - sigma_total_dire

        return {
            'mu_rad': mu_rad,
            'mu_dire': mu_dire,
            'mu_diff': mu_diff,
            'max_mu_rad': max_mu_rad,
            'max_mu_dire': max_mu_dire,
            'max_mu_diff': max_mu_diff,
            'std_mu_rad': std_mu_rad,
            'std_mu_dire': std_mu_dire,
            'std_diff': std_diff,
            'sigma_total_rad': sigma_total_rad,
            'sigma_total_dire': sigma_total_dire,
            'sigma_total_diff': sigma_total_diff
        }
    
    def get_avg_team_ordinal(self, players: list[dict], team: int, live: bool = True) -> float:
        """
        Returns the mean ordinal rating for a team's players, None is no players are found
        """
        if live:
            team_players = [p for p in players if p.get('team') == team]
        else:
            is_radiant = (team == 0)
            team_players = [p for p in players if p.get('isRadiant') == is_radiant]
            
        if not team_players:
            return None

        account_ids = [p.get('account_id') or p.get('steamAccountId') for p in team_players]
        valid_ids = [aid for aid in account_ids if aid is not None]
        
        if not valid_ids:
            return None

        ratings_dict = self.get_ratings(valid_ids)
        
        ordinals = [
            ratings_dict[aid].ordinal()
            for aid in valid_ids
            if aid in ratings_dict
        ]
        
        return float(np.mean(ordinals)) if ordinals else None
    
    def update_ratings_from_match(self, match_id: int):
        """
        Calculates and persists rating changes for a finished match.
        """
        query = """
            SELECT mp."steamAccountId", mp."isRadiant", md."didRadiantWin"
            FROM match_players mp
            JOIN match_details md ON md.id = mp.match_id
            WHERE mp.match_id = :mid AND mp."steamAccountId" IS NOT NULL
        """
        rows = self.db.select(query, {"mid": match_id})
        if not rows: return

        radiant_win = rows[0][2]
        rad_ids = [r[0] for r in rows if r[1]]
        dire_ids = [r[0] for r in rows if not r[1]]

        all_ratings = self.get_ratings(rad_ids + dire_ids)
        rad_team = [all_ratings[pid] for pid in rad_ids]
        dire_team = [all_ratings[pid] for pid in dire_ids]

        if radiant_win:
            new_rad, new_dire = self.model.rate([rad_team, dire_team])
        else:
            new_dire, new_rad = self.model.rate([dire_team, rad_team])

        updates = []
        zipped_updates = list(zip(rad_ids, new_rad)) + list(zip(dire_ids, new_dire))
        for pid, rating in zipped_updates:
            updates.append({
                'account_id': pid,
                'mu': rating.mu,
                'sigma': rating.sigma,
                'ordinal': rating.ordinal()
            })
        try:
            df_updates = pd.DataFrame(updates)
            self.db.insert_df_into_table(
                df_updates, 
                "current_player_ratings", 
                conflict_cols=["account_id"]
            )
            for item in updates:
                self._rating_cache[item['account_id']] = self._create_rating_obj(item['mu'], item['sigma']) 
            logging.info(f"Successfully processed ratings for match {match_id}")
            
        except Exception as e:
            logging.error(f"Failed to persist ratings for match {match_id}: {e}")

    
