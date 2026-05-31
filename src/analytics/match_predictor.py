import logging
import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from openskill.models import PlackettLuce, PlackettLuceRating

class MatchPredictor:
    def __init__(self):
        self.win_model = joblib.load('src/ml_models/tuned_model.joblib')
        
    def predict_win_probability(self, features) -> float:
        """
        Returns Radiant win probability for a live match.
        """
        try:
            prob = self.win_model.predict(features)
            return prob
        except Exception as e:
            logging.warning(f'Failed to predict win probability: {e}')
            return None