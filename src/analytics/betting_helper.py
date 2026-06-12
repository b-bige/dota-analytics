class BettingHelper:
    @staticmethod
    def kelly_criterion(decimal_odds: float, win_proba: float) -> float:
        if not decimal_odds or decimal_odds <= 1.0 or not win_proba:
            return 0.0
        lose_proba = 1.0 - win_proba
        net_odds = (decimal_odds - 1.0)
        return (net_odds * win_proba - lose_proba) / net_odds