import logging
import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

class MatchPredictor:
    def __init__(self): #TODO: Add dynamic model choice
        self._win_model: Pipeline = joblib.load('src/ml_models/log_reg_model.joblib')

    def predict_win_probability(self, mu_diff, std_diff, max_mu_diff, sigma_total_diff, draft_diff) -> float | None:
        """
        Returns Radiant win probability for a live match.
        """
        try:
            features = pd.DataFrame([{
                'mu_diff': mu_diff,
                'std_diff': std_diff,
                'max_mu_diff': max_mu_diff,
                'sigma_total_diff': sigma_total_diff,
                'draft_diff': draft_diff
            }]).fillna(0)
            prob = self._win_model.predict_proba(features.values)[0][1]
            return float(prob)
        except Exception as e:
            logging.warning(f'Failed to predict win probability: {e}')
            return None