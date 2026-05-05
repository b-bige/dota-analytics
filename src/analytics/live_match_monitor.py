import threading
import time
import httpx
import os
import sys
from datetime import datetime
import pandas as pd
import numpy as np
import logging
from src.core.logger import setup_logger
listener = setup_logger(logfile_path='logs/live-match-monitor.log')
from src.api import OpenDotaClient
from src.database import DatabaseManager
from src.analytics.match_predictor import MatchPredictor
from src.analytics.draft_service import DraftService
from src.analytics.rating_system import RatingSystem
from cachetools import TTLCache

class LiveMatchMonitor:
    def __init__(
        self, 
        db: DatabaseManager, 
        draft_service: DraftService, 
        rating_system: RatingSystem,
        opendota_client: OpenDotaClient
    ):
        self.db = db
        self.draft_service = draft_service
        self.rating_service = rating_system
        self.league_cache = TTLCache(maxsize=100, ttl=3600)
        self.logo_cache = TTLCache(maxsize=500, ttl=86400)
        self.opendota_client = opendota_client

    def _sync_metadata(self, live_matches: list[dict]):
        """
        Fetches league names, team names, and team logos from the database.
        """
        league_ids = {m.get('league_id') for m in live_matches if m.get('league_id')}
        missing_league_ids = [lid for lid in league_ids if lid not in self.league_cache]

        if missing_league_ids:
            league_query = """
                SELECT id, "displayName" AS league_name 
                FROM league_details 
                WHERE id = ANY(:league_ids)
            """
            league_rows = self.db.select(query=league_query, params={"league_ids": missing_league_ids})
            for row in league_rows:
                self.league_cache[row[0]] = {"league_name": row[1]}

        team_ids = set()
        for m in live_matches:
            if m.get('team_id_radiant'):
                team_ids.add(m['team_id_radiant'])
            if m.get('team_id_dire'):
                team_ids.add(m['team_id_dire'])

        missing_team_ids = [tid for tid in team_ids if tid not in self.logo_cache]

        if missing_team_ids:
            team_query = """
                SELECT team_id, logo_url 
                FROM team_logos 
                WHERE team_id = ANY(:team_ids)
            """
            team_rows = self.db.select(query=team_query, params={"team_ids": missing_team_ids})
            for row in team_rows:
                self.logo_cache[row[0]] = {"logo_url": row[1]}

    def process_cycle(self, live_matches: list[dict]):
        """
        Processes a cycle of live matches, combines computed data, and prepares for bulk upsert.
        """
        if not live_matches:
            return

        self._sync_metadata(live_matches)
        match_updates = []
        for match in live_matches:
            match_id = match.get('match_id')
            league_id = match.get('league_id') 
            if league_id == 0 or not league_id: continue
            is_finished = match.get('deactivate_time') != 0 
            if not match_id:
                continue

            if not self.draft_service.draft_is_complete(match):
                continue

            rad_heroes, dire_heroes = self.draft_service.get_draft(match, live=True)
            patch = self.opendota_client.get_internal_game_version(match.get('activate_time'), self.db)
            draft_strength_rad = self.draft_service.compute_draft_strength(rad_heroes, dire_heroes, patch)
            draft_strength_dire = self.draft_service.compute_draft_strength(dire_heroes, rad_heroes, patch)

            rad_ordinal = self.rating_service.get_avg_team_ordinal(match.get('players', []), team=0, live=True)
            dire_ordinal = self.rating_service.get_avg_team_ordinal(match.get('players', []), team=1, live=True)

            if rad_ordinal is not None and dire_ordinal is not None:
                rad_win_prob = 1 / (1 + 10 ** (-(rad_ordinal - dire_ordinal) / 400))
            else:
                rad_win_prob = 0.50

            rad_id = int(match.get('team_id_radiant')) or 0
            dire_id = int(match.get('team_id_dire')) or 0
            start_time = datetime.fromtimestamp(match.get('activate_time', datetime.now())) #TODO Replace now
            match_updates.append({
                'match_id': match_id,
                'league_id': match.get('league_id'),
                'league_name': self.league_cache.get(match.get('league_id'), {}).get('league_name', 'Unknown'),
                'start_date_time': start_time,
                'radiant_id': rad_id,
                'dire_id': dire_id,
                'radiant_name': match.get('team_name_radiant', 'Radiant'),
                'dire_name': match.get('team_name_dire', 'Dire'),
                'radiant_logo': self.logo_cache.get(rad_id, {}).get('logo_url', ''),
                'dire_logo': self.logo_cache.get(dire_id, {}).get('logo_url', ''),
                'radiant_score': match.get('radiant_score', 0),
                'dire_score': match.get('dire_score', 0),
                'game_time': match.get('game_time', 0),
                'radiant_lead': match.get('radiant_lead', 0),
                'is_finished': is_finished,
                'status': 'active',
                'radiant_draft_score': draft_strength_rad,
                'dire_draft_score': draft_strength_dire,
                'avg_radiant_rating': rad_ordinal,
                'avg_dire_rating': dire_ordinal,
                'rad_win_predicted': rad_win_prob,
                'last_updated': pd.Timestamp.now()
            })

        if match_updates:
            df = pd.DataFrame(match_updates)
            self.db.insert_df_into_table(df, table_name="live_matches", conflict_cols=["match_id"])
            logging.info('Successfully updated live_matches table')
        else:
            logging.info('No matches to be updated')
        
        self.handle_finished()

    def load_leagues_cache(self):
        """Loads the needed league details into a dictionary for optimized performance."""
        self.leagues_cache = {row[0]: row[1] for row in self.db.select('SELECT id, "displayName" FROM league_details')}

    def handle_finished(self): 
        """
        Requests parsing if not yet parsed on idle or deactivated live matches
        and stores them in the database, and deletes them from live_matches when saved.
        """
        query = """
            SELECT match_id, status, job_id 
            FROM live_matches 
            WHERE (last_updated < NOW() - INTERVAL '30 minutes' AND status = 'active') 
               OR (last_updated < NOW() - INTERVAL '10 minutes' AND is_finished AND status = 'active')
               OR (status = 'pending_parse')
               OR (is_finished)
        """
        finished_matches = self.db.select_to_df(query)
        if finished_matches.empty:
            logging.info("No finished matches found to process.")
            return
        
        match_ids_to_delete = []
        table_names = [
            'match_details', 'match_death_events', 'match_pick_bans', 'match_tower_deaths', 
            'match_players', 'match_purchases', 'match_runes', 'match_wards'
        ]
        accumulated_storage = {table: [] for table in table_names}

        for row in finished_matches.itertuples(index=False):
            match_id = getattr(row, 'match_id', None)
            status = getattr(row, 'status', None)
            job_id = getattr(row, 'job_id', None)
            # try:
            if status == 'active':
                if self.opendota_client.is_parsed_match(match_id=match_id):
                    match_data = self.opendota_client.get_match(match_id, db_manager=self.db)   
                    for table in table_names:
                        data = match_data.get(table, [])
                        if type(data) == dict:
                            accumulated_storage[table].append(data)
                        else:
                            accumulated_storage[table].extend(data)
                        
                    match_ids_to_delete.append(match_id)
                    continue
                if job_id is None:
                    new_job = self.opendota_client.request_parse(match_id)
                    logging.info(f"New job_id for match {match_id}: {new_job}")  # add this
                    update_query = """
                        UPDATE live_matches 
                        SET status = 'pending_parse', job_id = :job_id 
                        WHERE match_id = :match_id
                    """
                    self.db.execute(update_query, {"job_id": new_job, "match_id": match_id})
                    continue
                if self.opendota_client.is_parsed_match(job_id=job_id):
                    match_data = self.opendota_client.get_match(match_id, db_manager=self.db)
                    for table in table_names:
                        data = match_data.get(table, [])
                        if type(data) == dict:
                            accumulated_storage[table].append(data)
                        else:
                            accumulated_storage[table].extend(data)
                        
                    match_ids_to_delete.append(match_id)
                    continue
            elif status == 'pending_parse':
                if self.opendota_client.is_parsed_match(job_id):
                    match_data = self.opendota_client.get_match(match_id, db_manager=self.db)
                    
                    for table in table_names:
                        data = match_data.get(table, [])
                        if type(data) == dict:
                            accumulated_storage[table].append(data)
                        else:
                            accumulated_storage[table].extend(data)
                        
                    match_ids_to_delete.append(match_id)
            # except Exception as e:
            #     logging.error(f"Error processing finished match {match_id}: {e}")
            
        self._save_parsed_data(accumulated_storage)
        
        if match_ids_to_delete:
            delete_query = "DELETE FROM live_matches WHERE match_id = ANY(:match_ids)"
            self.db.execute(delete_query, {"match_ids": match_ids_to_delete})
            logging.info(f"Successfully moved and cleared {len(match_ids_to_delete)} matches.")

    def _save_parsed_data(self, storage: dict[str, list]):
        """Saves aggregated data into respective tables."""
        for table, records in storage.items():
            if records:
                df = pd.DataFrame(records)
                if 'index' in df.columns:
                    df = df.drop(columns=['index'])
                if table == 'match_players':
                    df.to_csv('match_players.csv')
                self.db.insert_df_into_table(df, table_name=table, conflict_cols=['id'])     

    def run_forever(self, interval: float):
        while True:
            # try:
                all_live = monitor.opendota_client.request('live')
                self.process_cycle(all_live)
            # except Exception as e:
            #     logging.error(f"Live Monitor Error: {e}")
                time.sleep(interval)

if __name__ == '__main__':
    db_manager = DatabaseManager()
    monitor = LiveMatchMonitor(
        db=db_manager, 
        draft_service=DraftService(db_manager),
        rating_system=RatingSystem(db_manager), 
        opendota_client=OpenDotaClient()
    )
    monitor.run_forever(interval=60)