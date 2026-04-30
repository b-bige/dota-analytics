from openskill.models import PlackettLuce, PlackettLuceRating
import logging
import numpy as np
from database.dota_db import DotaDB

class RatingSystem:
    def __init__(self, db: DotaDB):
        self.db = db
        self._openskill_model = PlackettLuce(tau=0.5)
        self._openskill_ratings: dict[int, PlackettLuceRating] = {}
        self.load_rating_cache()

    def load_rating_cache(self):
        """
        Load all player ratings into memory.
        Call once on startup and after bulk rating updates.
        """
        logging.info("Loading player rating cache...")
        rows = self.db.select('SELECT account_id, mu, sigma, ordinal FROM current_player_ratings')
        self._rating_cache = {
            row[0]: (float(row[1]), float(row[2]), float(row[3]))
            for row in rows
        }
        # also rebuild openskill Rating objects for live updates
        self._openskill_ratings = {
            account_id: self._openskill_model.rating(mu=mu, sigma=sigma)
            for account_id, (mu, sigma, ordinal) in self._rating_cache.items()
        }
        logging.info(f"Rating cache loaded — {len(self._rating_cache):,} players.")

    def get_player_rating(self, account_id: int) -> PlackettLuceRating:
        """
        Returns the OpenSkill Rating object for a player.
        If unknown, creates a new default rating and adds to cache.
        """
        if account_id not in self._openskill_ratings:
            new_rating = self._openskill_model.rating()
            self._openskill_ratings[account_id] = new_rating
            self._rating_cache[account_id] = (
                new_rating.mu,
                new_rating.sigma,
                new_rating.ordinal()
            )
            logging.debug(f"New player {account_id} initialised with default rating.")
        return self._openskill_ratings[account_id]
    
    def get_avg_team_ordinal(self, players: list[dict], team: int, live=True) -> float | None:
        """
        Returns mean ordinal rating for a team's players.
        """
        if live:
            team_players = [p for p in players if p.get('team') == team]
        else:
            team_players = [p for p in players if p.get('isRadiant') == (team == 0)]
        if not team_players:
            return None
        ordinals = [
            self.get_player_rating(p['account_id']).ordinal()
            for p in team_players
            if p.get('account_id')
        ]
        return float(np.mean(ordinals)) if ordinals else None
    
    def update_ratings_from_match(self, match_id: int):
        """
        Called when a live match finishes and is parsed.
        Fetches player stats, updates ratings, persists to DB.
        """
        rows = self.db.select('''
            SELECT mp."steamAccountId", mp."isRadiant", md."didRadiantWin"
            FROM match_players mp
            JOIN match_details md ON md.id = mp.match_id
            WHERE mp.match_id = %s
            AND mp."steamAccountId" IS NOT NULL
        ''', params=(match_id,))

        if not rows:
            logging.warning(f"No player data found for match {match_id} — skipping rating update.")
            return

        radiant_win = rows[0][2]
        radiant_ids = [r[0] for r in rows if r[1] == True]
        dire_ids    = [r[0] for r in rows if r[1] == False]

        if not radiant_ids or not dire_ids:
            logging.warning(f"Missing team data for match {match_id} — skipping.")
            return

        radiant_ratings = [self.get_player_rating(pid) for pid in radiant_ids]
        dire_ratings    = [self.get_player_rating(pid) for pid in dire_ids]

        # update ratings
        if radiant_win:
            new_radiant, new_dire = self._openskill_model.rate([radiant_ratings, dire_ratings])
        else:
            new_dire, new_radiant = self._openskill_model.rate([dire_ratings, radiant_ratings])

        updated = []
        for pid, new_r in zip(radiant_ids + dire_ids, new_radiant + new_dire):
            self._openskill_ratings[pid] = new_r
            self._rating_cache[pid] = (new_r.mu, new_r.sigma, new_r.ordinal())
            updated.append((new_r.mu, new_r.sigma, new_r.ordinal(), pid))

        self.db.query_executemany('''
            INSERT INTO current_player_ratings (account_id, mu, sigma, ordinal, last_updated)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (account_id) DO UPDATE SET
                mu      = EXCLUDED.mu,
                sigma   = EXCLUDED.sigma,
                ordinal = EXCLUDED.ordinal,
                last_updated = CURRENT_TIMESTAMP
        ''', params=[(pid, mu, sigma, ord_) for mu, sigma, ord_, pid in updated])
        logging.info(f"Updated ratings for {len(updated)} players from match {match_id}.")