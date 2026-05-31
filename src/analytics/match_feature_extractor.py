import pandas as pd
import numpy as np
from .rating_system import RatingSystem
from .state_manager import StateManager
from .player_history_manager import PlayerHistoryManager

class MatchFeatureExtractor:
    def __init__(
        self, 
        state_manager: StateManager, 
        player_history_manager: PlayerHistoryManager,
        rating_service: RatingSystem 
    ):
        self.sm = state_manager
        self.pm = player_history_manager
        self.rating_service = rating_service

    def build_draft_feature_dict(self, rad_heroes, dire_heroes, rad_players, dire_players, major_patch, sub_patch):
        """
        Calculates all draft features and returns an ordered dict.
        """
        draft_features = {}
        for side, team_data, enemies in [
            ('rad', zip(rad_heroes, rad_players), dire_heroes), 
            ('dire', zip(dire_heroes, dire_players), rad_heroes)
        ]:
            h_wrs, ph_wrs = [], []
            
            for hero_id, account_id in team_data:
                global_hero_wr = self.sm.get_feature_score(hero_id, "hero")
                h_wrs.append(global_hero_wr)
                
                player_wr = self.pm.get_player_hero_wr(
                    account_id, hero_id, global_hero_wr, major_patch, sub_patch
                )
                ph_wrs.append(player_wr)
            
            if h_wrs:
                draft_features[f'{side}_hero_wr'] = np.mean(h_wrs)
                draft_features[f'max_{side}_hero_wr'] = np.max(h_wrs)
                draft_features[f'min_{side}_hero_wr'] = np.min(h_wrs)
                draft_features[f'{side}_player_hero_wr'] = np.mean(ph_wrs)
                draft_features[f'max_{side}_player_hero_wr'] = np.max(ph_wrs)
                draft_features[f'min_{side}_player_hero_wr'] = np.min(ph_wrs)
            else:
                draft_features.update({f'{side}_hero_wr': 0.5, f'max_{side}_hero_wr': 0.5, f'min_{side}_hero_wr': 0.5})
                draft_features.update({f'{side}_player_hero_wr': 0.5, f'max_{side}_player_hero_wr': 0.5, f'min_{side}_player_hero_wr': 0.5})
            
            heroes_list = rad_heroes if side == 'rad' else dire_heroes
            syns = [
                self.sm.get_feature_score(tuple(sorted((h1, h2))), "syn") 
                for i, h1 in enumerate(heroes_list) 
                for h2 in heroes_list[i+1:]
            ]
            draft_features[f'{side}_syn_wr'] = np.mean(syns) if syns else 0.5
            draft_features[f'max_{side}_syn_wr'] = np.max(syns) if syns else 0.5
            draft_features[f'min_{side}_syn_wr'] = np.min(syns) if syns else 0.5
            
            cnts = [
                self.sm.get_feature_score((h, e), "cnt") 
                for h in heroes_list for e in enemies
            ]
            draft_features[f'{side}_cnt_wr'] = np.mean(cnts) if cnts else 0.5
            draft_features[f'max_{side}_cnt_wr'] = np.max(cnts) if cnts else 0.5
            draft_features[f'min_{side}_cnt_wr'] = np.min(cnts) if cnts else 0.5

        draft_features['player_hero_wr_diff'] = draft_features['rad_player_hero_wr'] - draft_features['dire_player_hero_wr']
        draft_features['hero_wr_diff'] = draft_features['rad_hero_wr'] - draft_features['dire_hero_wr']
        draft_features['syn_wr_diff'] = draft_features['rad_syn_wr'] - draft_features['dire_syn_wr']
        draft_features['cnt_wr_diff'] = draft_features['rad_cnt_wr'] - draft_features['dire_cnt_wr']

        sorted_features = {k: draft_features[k] for k in sorted(draft_features.keys())}
        
        return sorted_features
        
    def extract_pure_draft_strength(self, feature_df, model, baseline_mu=30.0):
        """
        Takes the full 40 features, neutralizes all player-rating differentials,
        and returns a clean, single score representing Radiant's draft advantage.
        """
        win_model = model.win_model
        contributions = win_model.predict(feature_df, pred_contrib=True)[0]
        
        feature_names = win_model.feature_name()
        
        draft_log_odds_rad = 0.0
        for i, feature in enumerate(feature_names):
            if not any(rating_word in feature for rating_word in ['mu', 'sigma', 'std']):
                draft_log_odds_rad += contributions[i]
                
        draft_log_odds_dire = -draft_log_odds_rad
        
        prob_rad = 1 / (1 + np.exp(-draft_log_odds_rad))
        prob_dire = 1 / (1 + np.exp(-draft_log_odds_dire))
        
        return int(round(prob_rad * 100)), int(round(prob_dire * 100))
