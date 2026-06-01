import pandas as pd
import numpy as np
from .rating_system import RatingSystem
from .state_manager import StateManager
from .player_history_manager import PlayerHistoryManager
from src.database import DatabaseManager

class MatchFeatureExtractor:
    def __init__(
        self, 
        rating_service: RatingSystem,
        state_manager: StateManager | None = None, 
        player_history_manager: PlayerHistoryManager | None = None
    ):
        self.sm = state_manager
        self.pm = player_history_manager
        self.rating_service = rating_service

    def build_draft_feature_dict(self, rad_heroes, dire_heroes, rad_players, dire_players, major_patch, sub_patch):
        """
        Calculates all draft features and returns an ordered dict.
        """
        if not self.sm or not self.pm:
            raise AttributeError('State Manager or Player History Manager attributes were not assigned')
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
    
    def batch_build_draft_features(self, match_params_list, db: DatabaseManager, sm_alpha=20, pm_alpha=5):
        """
        Calculates all draft features for a batch of matches and returns a dict of {match_id: sorted_features_dict}
        """
        all_heroes = set()
        all_players = set()
        all_patches = set()

        for m in match_params_list:
            all_heroes.update(m['rad_heroes'])
            all_heroes.update(m['dire_heroes'])
            all_players.update(m['rad_players'])
            all_players.update(m['dire_players'])
            all_patches.add(m['major_patch'])
            all_patches.add(m['sub_patch'])

        if not all_heroes:
            return {}

        heroes_list = list(all_heroes)
        players_list = list(all_players)
        patches_list = list(all_patches)
        keys_b_list = heroes_list + [-1] 

        sm_hist_rows = db.select("""
            SELECT stat_type, key_a, key_b, wins, games FROM state_manager_history
            WHERE key_a = ANY(:heroes_list) AND key_b = ANY(:keys_b_list)
        """, {'heroes_list': heroes_list, 'keys_b_list': keys_b_list})

        sm_stats_rows = db.select("""
            SELECT scope, stat_type, key_a, key_b, wins, games FROM state_manager_stats
            WHERE key_a = ANY(:heroes_list) AND key_b = ANY(:keys_b_list)
        """, {'heroes_list': heroes_list, 'keys_b_list': keys_b_list})

        pm_hist_rows = db.select("""
            SELECT account_id, hero_id, wins, games FROM player_manager_history
            WHERE account_id = ANY(:account_ids) AND hero_id = ANY(:hero_ids)
        """, {'account_ids': players_list, 'hero_ids': heroes_list})

        pm_stats_rows = db.select("""
            SELECT scope, account_id, hero_id, patch, wins, games FROM player_manager_stats
            WHERE account_id = ANY(:account_ids) AND hero_id = ANY(:hero_ids) AND patch = ANY(:patches)
        """, {'account_ids': players_list, 'hero_ids': heroes_list, 'patches': patches_list})

        sm_cache = {'history': {}, 'major_patch': {}, 'sub_patch': {}}
        pm_cache = {'history': {}, 'major_patch': {}, 'sub_patch': {}}

        for row in sm_hist_rows:
            sm_cache['history'][(row[0], row[1], row[2])] = (row[3], row[4])
        for row in sm_stats_rows:
            sm_cache[row[0]][(row[1], row[2], row[3])] = (row[4], row[5])
            
        for row in pm_hist_rows:
            pm_cache['history'][(row[0], row[1])] = (row[2], row[3])
        for row in pm_stats_rows:
            pm_cache[row[0]][(row[1], row[2], row[3])] = (row[4], row[5])

        results = {}

        for m in match_params_list:
            df = {} 
            
            for side, team_data, enemies in [
                ('rad', zip(m['rad_heroes'], m['rad_players']), m['dire_heroes']), 
                ('dire', zip(m['dire_heroes'], m['dire_players']), m['rad_heroes'])
            ]:
                h_wrs, ph_wrs = [], []
                
                for hero_id, account_id in team_data:
                    hw, hg = sm_cache['history'].get(('hero', hero_id, -1), (0, 0))
                    mw, mg = sm_cache['major_patch'].get(('hero', hero_id, -1), (0, 0))
                    sw, sg = sm_cache['sub_patch'].get(('hero', hero_id, -1), (0, 0))

                    hist_wr = hw / hg if hg > 0 else 0.5
                    major_wr = (mw + sm_alpha * hist_wr) / (mg + sm_alpha)
                    global_hero_wr = (sw + sm_alpha * major_wr) / (sg + sm_alpha)
                    h_wrs.append(global_hero_wr)
                    
                    if not account_id or account_id == 0:
                        ph_wrs.append(global_hero_wr)
                    else:
                        phw, phg = pm_cache['history'].get((account_id, hero_id), (0, 0))
                        pmw, pmg = pm_cache['major_patch'].get((account_id, hero_id, m['major_patch']), (0, 0))
                        psw, psg = pm_cache['sub_patch'].get((account_id, hero_id, m['sub_patch']), (0, 0))

                        p_hist_wr = phw / phg if phg > 0 else global_hero_wr
                        p_major_wr = (pmw + pm_alpha * p_hist_wr) / (pmg + pm_alpha)
                        player_wr = (psw + pm_alpha * p_major_wr) / (psg + pm_alpha)
                        ph_wrs.append(player_wr)

                if h_wrs:
                    df[f'{side}_hero_wr'] = np.mean(h_wrs)
                    df[f'max_{side}_hero_wr'] = np.max(h_wrs)
                    df[f'min_{side}_hero_wr'] = np.min(h_wrs)
                    df[f'{side}_player_hero_wr'] = np.mean(ph_wrs)
                    df[f'max_{side}_player_hero_wr'] = np.max(ph_wrs)
                    df[f'min_{side}_player_hero_wr'] = np.min(ph_wrs)
                else:
                    df.update({f'{side}_hero_wr': 0.5, f'max_{side}_hero_wr': 0.5, f'min_{side}_hero_wr': 0.5})
                    df.update({f'{side}_player_hero_wr': 0.5, f'max_{side}_player_hero_wr': 0.5, f'min_{side}_player_hero_wr': 0.5})

                heroes_list = m['rad_heroes'] if side == 'rad' else m['dire_heroes']
                
                syns = []
                for i, h1 in enumerate(heroes_list):
                    for h2 in heroes_list[i+1:]:
                        ka, kb = tuple(sorted((h1, h2)))
                        hw, hg = sm_cache['history'].get(('syn', ka, kb), (0, 0))
                        mw, mg = sm_cache['major_patch'].get(('syn', ka, kb), (0, 0))
                        sw, sg = sm_cache['sub_patch'].get(('syn', ka, kb), (0, 0))
                        h_wr = hw / hg if hg > 0 else 0.5
                        m_wr = (mw + sm_alpha * h_wr) / (mg + sm_alpha)
                        syns.append((sw + sm_alpha * m_wr) / (sg + sm_alpha))

                df[f'{side}_syn_wr'] = np.mean(syns) if syns else 0.5
                df[f'max_{side}_syn_wr'] = np.max(syns) if syns else 0.5
                df[f'min_{side}_syn_wr'] = np.min(syns) if syns else 0.5

                cnts = []
                for h in heroes_list:
                    for e in enemies:
                        hw, hg = sm_cache['history'].get(('cnt', h, e), (0, 0))
                        mw, mg = sm_cache['major_patch'].get(('cnt', h, e), (0, 0))
                        sw, sg = sm_cache['sub_patch'].get(('cnt', h, e), (0, 0))
                        h_wr = hw / hg if hg > 0 else 0.5
                        m_wr = (mw + sm_alpha * h_wr) / (mg + sm_alpha)
                        cnts.append((sw + sm_alpha * m_wr) / (sg + sm_alpha))

                df[f'{side}_cnt_wr'] = np.mean(cnts) if cnts else 0.5
                df[f'max_{side}_cnt_wr'] = np.max(cnts) if cnts else 0.5
                df[f'min_{side}_cnt_wr'] = np.min(cnts) if cnts else 0.5

            df['player_hero_wr_diff'] = df['rad_player_hero_wr'] - df['dire_player_hero_wr']
            df['hero_wr_diff'] = df['rad_hero_wr'] - df['dire_hero_wr']
            df['syn_wr_diff'] = df['rad_syn_wr'] - df['dire_syn_wr']
            df['cnt_wr_diff'] = df['rad_cnt_wr'] - df['dire_cnt_wr']

            results[m['match_id']] = {k: df[k] for k in sorted(df.keys())}

        return results
        
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
