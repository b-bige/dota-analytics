import logging
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

class MatchPredictor:
    def __init__(self): #TODO: Add dynamic model choice
        self._win_model = joblib.load('src/ml_models/log_reg_model.joblib')

    def predict_win_probability(self, radiant_draft_score, dire_draft_score, avg_rad_rating, avg_dire_rating) -> float | None:
        """
        Returns Radiant win probability for a live match.
        Returns 0.5 if not enough features are available.
        """
        if avg_rad_rating is None or avg_dire_rating is None:
            return 0.5

        features = pd.DataFrame([{
            'rating_diff':    avg_rad_rating - avg_dire_rating,
            'draft_diff':     radiant_draft_score - dire_draft_score
        }]).fillna(0)

        prob = self._win_model.predict(features.values)[0][1] 
        return float(prob)