import threading
import time
import httpx
import os
import sys
from datetime import datetime
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))
sys.path.append(os.path.abspath('./src/dashboard'))

import logging
from core.logger import setup_logger
listener = setup_logger(logfile_path='logs/live-match-monitor.log')
from database.dota_db import DotaDB
from analytics.match_predictor import MatchPredictor
from analytics.draft_analyzer import DraftAnalyzer
from analytics.rating_system import RatingSystem

class LiveMatchMonitor:
    def __init__(self, db: DotaDB):
        self.db = db
        self.match_predictor = MatchPredictor()
        self.draft_analyzer = DraftAnalyzer(db)
        self.rating_system = RatingSystem(db)
        self.httpx_client = httpx.Client()
        self.load_logo_cache()
        self.load_leagues_cache()
        self.rating_cache = {}
        self.draft_cache = {}
        self.predict_cache = {}

    def load_logo_cache(self):
        """Loads the team logos table into a dictionary for optimized performance."""
        self.logo_cache = {row[0]: row[1] for row in self.db.select('SELECT team_id, logo_url FROM team_logos')}

    def load_leagues_cache(self):
        """Loads the needed league details into a dictionary for optimized performance."""
        self.leagues_cache = {row[0]: row[1] for row in self.db.select('SELECT id, "displayName" FROM league_details')}

    def update_live_database(self):
        """
        Fetches top live games from OpenDota API, filters for ones that have a league ID attached.
        Calculates features when the data is available for them, and prepares a list of parameters to update
        the live matches table.
        """
        #TODO optimize
        all_live = self.db.fetch_opendota(self.httpx_client, 'live')
        missing_teams = {m.get('team_id_radiant') for m in all_live} | \
                    {m.get('team_id_dire') for m in all_live}
        missing_teams = {tid for tid in missing_teams if tid and tid not in self.logo_cache.keys()}
        archived_ids = {r[0] for r in self.db.select('SELECT match_id FROM archive_live_match_ids')}

        scored_ids = {r[0] for r in self.db.select(
            "SELECT match_id FROM live_matches WHERE radiant_draft_score IS NOT NULL AND status = 'active'"
        )}

        rated_ids = {r[0] for r in self.db.select(
            "SELECT match_id FROM live_matches WHERE avg_radiant_rating IS NOT NULL AND status = 'active'"
        )}
        predicted_ids = {r[0] for r in self.db.select(
            "SELECT match_id FROM live_matches WHERE rad_win_predicted IS NOT NULL AND status = 'active'"
        )}
        insert_params = []
        for m in all_live:
            league_id = m.get('league_id') 
            if league_id == 0 or not league_id: continue
            is_finished = m.get('deactivate_time') != 0 
            
            m_id = m['match_id']
            if m_id in archived_ids:
                continue
            league_name = self.leagues_cache.get(league_id, None)
            if not league_name:
                league_name = self.get_league_details(league_id)
                self.leagues_cache[league_id] = league_name
            start_time = datetime.fromtimestamp(m.get('activate_time'))
            r_id = int(m.get('team_id_radiant')) or 0
            d_id = int(m.get('team_id_dire')) or 0
            radiant_logo = self.logo_cache.get(r_id, None)
            dire_logo = self.logo_cache.get(d_id, None)
            if not radiant_logo:
                radiant_logo = self.get_team_logo(r_id)
                self.logo_cache[r_id] = radiant_logo
            if not dire_logo:
                dire_logo = self.get_team_logo(d_id)
                self.logo_cache[d_id] = dire_logo

            radiant_draft_score, dire_draft_score = self.draft_cache.get(m_id, (None, None))
            avg_radiant_rating, avg_dire_rating = self.rating_cache.get(m_id, (None, None))
            rad_win_predicted = self.predict_cache.get(m_id, None)

            draft_complete = self.draft_analyzer.draft_is_complete(m)

            if m_id not in scored_ids and draft_complete:
                try:
                    patch = self.db.get_current_patch()
                    radiant_heroes, dire_heroes = self.draft_analyzer.get_draft(m)
                    radiant_draft_score = self.draft_analyzer.compute_draft_strength(radiant_heroes, dire_heroes, patch)
                    dire_draft_score    = self.draft_analyzer.compute_draft_strength(dire_heroes, radiant_heroes, patch)
                    if radiant_draft_score is not None and dire_draft_score is not None:
                        scored_ids.add(m_id)
                        self.draft_cache[m_id] = (radiant_draft_score, dire_draft_score)
                except Exception as e:
                    logging.warning(f"Failed to calculate draft strength for match {m_id}: {e}")

            if m_id not in rated_ids and draft_complete:
                try:
                    players = m.get('players', [])
                    avg_radiant_rating = self.rating_system.get_avg_team_ordinal(players, team=0)
                    avg_dire_rating    = self.rating_system.get_avg_team_ordinal(players, team=1)
                    if avg_radiant_rating is not None and avg_dire_rating is not None:
                        rated_ids.add(m_id)
                        self.rating_cache[m_id] = (avg_radiant_rating, avg_dire_rating)
                        logging.info(f"Ratings for match {m_id} — "
                                    f"Radiant: {avg_radiant_rating:.1f}, Dire: {avg_dire_rating:.1f}")
                except Exception as e:
                    logging.warning(f"Failed to calculate ratings for match {m_id}: {e}")

            if m_id not in predicted_ids and draft_complete:
                if all(v is not None for v in [radiant_draft_score, dire_draft_score, avg_radiant_rating, avg_dire_rating]):
                    rad_win_predicted = self.match_predictor.predict_win_probability(
                        radiant_draft_score, 
                        dire_draft_score, 
                        avg_radiant_rating, 
                        avg_dire_rating
                    )
                    self.predict_cache[m_id] = rad_win_predicted
                    predicted_ids.add(m_id)
            insert_params.append((
                m_id, league_id, league_name, start_time,
                m.get('team_id_radiant'), m.get('team_id_dire'),
                m.get('team_name_radiant', 'Radiant'), m.get('team_name_dire', 'Dire'),
                radiant_logo, dire_logo, m.get('radiant_score', 0),
                m.get('dire_score', 0), m.get('game_time', 0), m.get('radiant_lead', 0),
                is_finished, 'active',
                radiant_draft_score, dire_draft_score,
                avg_radiant_rating, avg_dire_rating,
                rad_win_predicted
            ))
        query = """
            INSERT INTO live_matches (match_id, league_id, league_name,
            start_date_time, radiant_id, dire_id,
            radiant_name, dire_name,
            radiant_logo, dire_logo, radiant_score, dire_score,
            game_time, radiant_lead, is_finished, status,
            radiant_draft_score, dire_draft_score,
            avg_radiant_rating, avg_dire_rating,
            rad_win_predicted, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (match_id) DO UPDATE SET
                radiant_score      = EXCLUDED.radiant_score,
                dire_score         = EXCLUDED.dire_score,
                game_time          = EXCLUDED.game_time,
                radiant_lead       = EXCLUDED.radiant_lead,
                is_finished        = EXCLUDED.is_finished,
                last_updated       = CURRENT_TIMESTAMP,
                radiant_draft_score = COALESCE(live_matches.radiant_draft_score, EXCLUDED.radiant_draft_score),
                dire_draft_score    = COALESCE(live_matches.dire_draft_score,    EXCLUDED.dire_draft_score),
                avg_radiant_rating  = COALESCE(live_matches.avg_radiant_rating,  EXCLUDED.avg_radiant_rating),
                avg_dire_rating     = COALESCE(live_matches.avg_dire_rating,      EXCLUDED.avg_dire_rating),
                rad_win_predicted = EXCLUDED.rad_win_predicted
            WHERE live_matches.game_time IS DISTINCT FROM EXCLUDED.game_time;
        """
        self.db.query_executemany(query, params=insert_params)

        # CLEANUP: See if match is parsed yet on opendota, if not then request it and wait, 
        # save the details and drop the matches
        self.handle_finished()

    def handle_finished(self):
        """
        Requests parsing if not yet parsed on idle or deactivated live matches and stores them in the database,
        and deletes them from live_matches when saved.
        """
        query = """
        SELECT match_id FROM live_matches WHERE last_updated < NOW() - INTERVAL '15 minutes' AND status = 'active' 
        UNION
        SELECT match_id FROM live_matches WHERE (last_updated < NOW() - INTERVAL '10 minutes') AND is_finished AND status = 'active'
        """
        active_ids = {r[0] for r in self.db.select(query)}
        query = "SELECT match_id, job_id FROM live_matches WHERE status = 'pending_parse'"
        pending = self.db.select_to_df(query, columns=['match_id', 'job_id'])
        for mid in active_ids:
            try:
                self.insert_update_processed_match(mid)
                logging.info(f'Saved finished match ID {mid} into database')
            except:
                job_id = self.db.request_parse_opendota(self.httpx_client, mid)
                self.db.query_execute(
                    "UPDATE live_matches SET status = 'pending_parse', job_id = %s WHERE match_id = %s", 
                    params=(job_id, mid))
        for _, row in pending.iterrows():
            mid = int(row['match_id'])
            try:
                if self.db.is_match_parsed_opendota(self.httpx_client, mid):
                    self.insert_update_processed_match(mid)
                    logging.info(f'Saved finished match ID {mid} into database')
            except Exception as e:
                self.db.query_execute(
                    "UPDATE live_matches SET status = 'failed_parse' WHERE match_id = %s",
                    params=(mid, )
                )
                logging.error(f'Failed to fetch parsed data for match ID {mid}')
        # self.db.query_execute('REFRESH MATERIALIZED VIEW hero_pick_ban_stats;')
        # self.db.query_execute('REFRESH MATERIALIZED VIEW hero_winrate_stats')

    def insert_update_processed_match(self, match_id: int):
        """
        Handles the fetching of a finished match ID, and updates the tables related to
        live matches.
        """
        ##TODO: optimize
        self.db.fetch_match_opendota(self.httpx_client, match_id)
        self.db.query_execute('INSERT INTO archive_live_match_ids VALUES (%s)', params=(match_id, ))
        self.db.query_execute("UPDATE live_matches SET status = 'fetched_opendota' WHERE match_id = %s", params=(match_id, ))
        self.rating_system.update_ratings_from_match(match_id)
        query = '''
            UPDATE match_details 
            SET avg_radiant_rating = %s, avg_dire_rating = %s, 
            radiant_draft_score = %s, dire_draft_score = %s
            WHERE id = %s
        '''
        self.db.query_execute(
            query, 
            params=(
                self.rating_cache[match_id][0], 
                self.rating_cache[match_id][1], 
                self.draft_cache[match_id][0],  
                self.draft_cache[match_id][1],  
                match_id                        
            )                     
        )
        self.rating_cache.pop(match_id, None)
        self.draft_cache.pop(match_id, None)
        self.predict_cache.pop(match_id, None)

    def get_league_details(self, league_id: int) -> str:
        """Returns league name. Fetches from API and saves the details after to DB."""
        result = self.db.fetch_opendota(self.httpx_client, f'leagues/{league_id}')
        if result:
            try:
                query = 'INSERT INTO league_details (id, "displayName", tier) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING'
                self.db.query_execute(query, params=(result['leagueid'], result['name'], str(result['tier']).upper()))
                return result['name']
            except Exception as e:
                logging.error(f'Failed to fetch league details: {e}')
                return 'Unknown League'
        return 'Unknown League'

    def get_team_logo(self, team_id: int) -> str:
        """Returns a URL. Fetches from API and saves the details after to DB."""
        if not team_id or team_id == 0:
            return '/assets/no_image.svg'
        result = self.db.fetch_opendota(self.httpx_client, f'teams/{team_id}')
        if result:
            try:       
                url = result.get("logo_url") or "/assets/no_image.svg"
                self.db.query_execute(
                    "INSERT INTO team_logos (team_id, logo_url) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    params=(team_id, url)
                )
                self.logo_cache[team_id] = url
                return url
            except Exception as e:
                logging.error(f"Failed to fetch team logo: {e}")
                return "/assets/no_image.svg"

    def run_forever(self, interval: float):
        while True:
            try:
                self.update_live_database()
            except Exception as e:
                logging.error(f"Live Monitor Error: {e}")
            time.sleep(interval)

if __name__ == '__main__':
    monitor = LiveMatchMonitor(DotaDB())
    monitor.run_forever(interval=180)