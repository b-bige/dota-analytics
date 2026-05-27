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
from src.api import SteamApiClient, OpenDotaClient
from src.database import DatabaseManager
from src.analytics.match_predictor import MatchPredictor
from src.analytics.draft_service import DraftService
from src.analytics.rating_system import RatingSystem
from cachetools import TTLCache
from openskill.models import PlackettLuce, PlackettLuceRating
logging.getLogger("httpx").setLevel(logging.WARNING)

class LiveMatchMonitor:
    def __init__(
        self, 
        db: DatabaseManager, 
        draft_service: DraftService, 
        rating_system: RatingSystem,
        match_predictor: MatchPredictor,
        steam_api_client: SteamApiClient,
        opendota_client: OpenDotaClient
    ):
        self.db = db
        self.draft_service = draft_service
        self.rating_service = rating_system
        self.match_predictor = match_predictor
        self.league_cache = TTLCache(maxsize=100, ttl=3600)
        self.logo_cache = TTLCache(maxsize=500, ttl=86400)
        self.steam_api_client = steam_api_client
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
            radiant_team = m.get('radiant_team', None)
            if radiant_team:
                rad_id = radiant_team.get('team_id', None)
                if rad_id:
                    team_ids.add(rad_id)
            dire_team = m.get('dire_team', None)
            if dire_team:
                dire_id = dire_team.get('team_id', None)
                if dire_id:
                    team_ids.add(dire_id)

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

    def process_cycle(self, live_matches: list[dict], timestamp: float):
        """
        Processes a cycle of live matches, calculates ratings,  stores them in the live_matches table and moves inactive ones 
        to finished status.

        Parameters
        ----------
        live_matches : list[dict]
        A list of live matches dictionary from Valve's Steam Web API.
        timestamp : float
        A timestamp taken right after the API call is returned for game start time calculation.
        """
        #TODO: Make a rating updating script for the new Valve pipeline
        #TODO: create methods for the code for cleanup
        if not live_matches:
            return
        self._sync_metadata(live_matches)
        match_updates = []
        for match in live_matches:
            match_id = match.get('match_id')

            league_id = match.get('league_id') 
            if league_id == 0 or not league_id: continue
            if not match_id:
                continue
            if not self.draft_service.draft_is_complete(match):
                continue
            if not match.get('radiant_team') or not match.get('dire_team'):
                continue # Not showing matches without data about teams for now

            rad_player_ids = [p['account_id'] for p in match.get('players', []) if p.get('team') == 0]
            dire_player_ids = [p['account_id'] for p in match.get('players', []) if p.get('team') == 1]
            scoreboard = match.get('scoreboard')
            game_time = scoreboard.get('duration')
            start_time = timestamp - game_time

            ### Model feature: mu_diff 
            rad_ratings = self.rating_service.get_ratings(rad_player_ids)
            dire_ratings = self.rating_service.get_ratings(dire_player_ids)
            radiant_mus = np.array([r.mu for r in rad_ratings.values()])
            dire_mus = np.array([r.mu for r in dire_ratings.values()])
            mu_diff = np.mean(radiant_mus) - np.mean(dire_mus)

            ### Model feature: std_diff
            std_diff = np.std(radiant_mus) - np.std(dire_mus)

            ### Model feature: max_mu_diff
            max_mu_diff = np.max(radiant_mus) - np.max(dire_mus)

            ### Model feature: sigma_total_diff
            radiant_sigma = np.array([r.sigma for r in rad_ratings.values()])
            dire_sigma = np.array([r.sigma for r in dire_ratings.values()])
            sigma_total_diff = np.sum(radiant_sigma) - np.sum(dire_sigma)

            ### Model feature: draft_diff
            rad_heroes, dire_heroes = self.draft_service.get_draft(match, live=True)
            patch = self.opendota_client.get_internal_game_version(start_time, self.db)
            draft_strength_rad = self.draft_service.compute_draft_strength(rad_heroes, dire_heroes, patch)
            draft_strength_dire = self.draft_service.compute_draft_strength(dire_heroes, rad_heroes, patch)
            draft_diff = draft_strength_rad - draft_strength_dire

            rad_ordinal = self.rating_service.get_avg_team_ordinal(match.get('players', []), team=0, live=True)
            dire_ordinal = self.rating_service.get_avg_team_ordinal(match.get('players', []), team=1, live=True)

            rad_win_prob = self.match_predictor.predict_win_probability(
                mu_diff=mu_diff,
                std_diff=std_diff,
                max_mu_diff=max_mu_diff,
                sigma_total_diff=sigma_total_diff,
                draft_diff=draft_diff
            )

            rad_team = match.get('radiant_team')
            dire_team = match.get('dire_team')
            rad_id = int(rad_team.get('team_id')) or 0
            dire_id = int(dire_team.get('team_id')) or 0
            rad_name = rad_team.get('team_name', 'Radiant Unknown')
            dire_name = dire_team.get('team_name', 'Dire Unknown')
            rad_score = scoreboard.get('radiant').get('score')
            dire_score = scoreboard.get('dire').get('score')
            league_name = self.league_cache.get(match.get('league_id'), {}).get('league_name')
            if not league_name:
                league_name = self.fetch_league_details(league_id)
            rad_networth = np.array([p.get('net_worth') for p in scoreboard.get('radiant').get('players')])
            dire_networth = np.array([p.get('net_worth') for p in scoreboard.get('dire').get('players')])
            radiant_lead = np.sum(rad_networth) - np.sum(dire_networth)
            match_updates.append({
                'match_id': match_id,
                'league_id': league_id,
                'league_name': self.league_cache.get(match.get('league_id'), {}).get('league_name', 'Unknown'),
                'start_date_time': datetime.fromtimestamp(start_time),
                'radiant_id': rad_id,
                'dire_id': dire_id,
                'radiant_name': rad_name,
                'dire_name': dire_name,
                'radiant_logo': self.logo_cache.get(rad_id, {}).get('logo_url', ''),
                'dire_logo': self.logo_cache.get(dire_id, {}).get('logo_url', ''),
                'radiant_score': rad_score,
                'dire_score': dire_score,
                'game_time': int(round(game_time)),
                'radiant_lead': radiant_lead,
                'is_finished': False, #TODO: figure out if we need this
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
            self.db.insert_df_into_table(
                df, 
                table_name="live_matches", 
                conflict_cols=["match_id"],
                avoid_cols=["start_date_time"]
            )
            logging.info('Successfully updated live_matches table')
        else:
            logging.info('No matches to be updated')

        ### Setting status to 'finished' and is_finished to TRUE for inactive matches 
        query = """
            UPDATE live_matches 
            SET status = 'finished', is_finished = TRUE 
            WHERE status = 'active' 
                AND last_updated < NOW() - INTERVAL '15 minutes';
        """
        self.db.execute(query)
    
    def handle_finished(self): 
        """
        Requests parsing if not yet parsed on idle or deactivated live matches
        and stores them in the database, and deletes them from live_matches when saved.
        """
        #NOTE: Function became redundant because Valve's Official API has been implemented, while I figure out
        # how and when to fetch the finished matches from other APIs they are just set to status = 'finished' for now
        query = """
            SELECT match_id, status, job_id, avg_radiant_rating, avg_dire_rating, radiant_draft_score, dire_draft_score
            FROM live_matches 
            WHERE (last_updated < NOW() - INTERVAL '30 minutes' AND status = 'active') 
               OR (last_updated < NOW() - INTERVAL '10 minutes' AND is_finished AND status = 'active')
               OR (status = 'pending_parse')
            ORDER BY start_date_time ASC
        """ #NOTE: Ascending order for proper chronological rating calculation
        finished_matches = self.db.select_to_df(query)
        if finished_matches.empty:
            logging.info("No finished matches found to process.")
            return
        
        match_ids_fetched = []
        match_ids_missing_detail = []
        table_names = [
            'match_details', 'match_death_events', 'match_pick_bans', 'match_tower_deaths', 
            'match_players', 'match_purchases', 'match_runes', 'match_wards'
        ]
        accumulated_storage = {table: [] for table in table_names}

        for row in finished_matches.itertuples(index=False):
            match_id = getattr(row, 'match_id', None)
            status = getattr(row, 'status', None)
            job_id = getattr(row, 'job_id', None)
            avg_radiant_rating = getattr(row, 'avg_radiant_rating', None)
            avg_dire_rating = getattr(row, 'avg_dire_rating', None)
            radiant_draft_score = getattr(row, 'radiant_draft_score', None)
            dire_draft_score = getattr(row, 'dire_draft_score', None)
            #TODO: Get rid of try-catch, find why no detail
            try:
                if status == 'active' or status == 'pending_parse':
                    match_data = self.opendota_client.get_match(match_id, db_manager=self.db)   
                    for table in table_names:
                        data = match_data.get(table, [])
                        if table == 'match_details':
                            data.update(
                                {
                                    'avg_radiant_rating': avg_radiant_rating,
                                    'avg_dire_rating': avg_dire_rating,
                                    'radiant_draft_score': radiant_draft_score,
                                    'dire_draft_score': dire_draft_score
                                }
                            )
                            accumulated_storage[table].append(data)
                        elif type(data) == dict:
                            accumulated_storage[table].append(data)
                        else:
                            accumulated_storage[table].extend(data)  
                    match_ids_fetched.append(match_id)
                    continue
                #NOTE: This part is commented out because I ran into rate limiting issues. Requesting a parse counts
                #NOTE: 10x as much than a simple match request, and for now this feature is dropped.
                #     if job_id is None:
                #         # new_job = self.opendota_client.request_parse(match_id)
                #         # logging.info(f"New job_id for match {match_id}: {new_job}") 
                #         # update_query = """
                #         #     UPDATE live_matches 
                #         #     SET status = 'pending_parse', job_id = :job_id 
                #         #     WHERE match_id = :match_id
                #         # """
                #         # self.db.execute(update_query, {"job_id": new_job, "match_id": match_id})
                #         # continue
                #     if self.opendota_client.is_parsed_match(job_id=job_id):
                #         match_data = self.opendota_client.get_match(match_id, db_manager=self.db)
                #         for table in table_names:
                #             data = match_data.get(table, [])
                #             if type(data) == dict:
                #                 accumulated_storage[table].append(data)
                #             else:
                #                 accumulated_storage[table].extend(data)
                            
                #         match_ids_to_delete.append(match_id)
                #         continue
                # elif status == 'pending_parse':
                #     if self.opendota_client.is_parsed_match(job_id=job_id):
                #         match_data = self.opendota_client.get_match(match_id, db_manager=self.db)
                        
                #         for table in table_names:
                #             data = match_data.get(table, [])
                #             if type(data) == dict:
                #                 accumulated_storage[table].append(data)
                #             else:
                #                 accumulated_storage[table].extend(data)
                            
                #         match_ids_to_delete.append(match_id)
            except Exception as e:
                match_ids_missing_detail.append(match_id)
                logging.error(f"Error processing finished match {match_id}: {e}")
        self._save_parsed_data(accumulated_storage)
        if match_ids_fetched:
            update_query = "UPDATE live_matches SET status = 'fetched_from_opendota' WHERE match_id = ANY(:match_ids)"
            self.db.execute(update_query, {'match_ids': match_ids_fetched})
            for mid_fetched in match_ids_fetched:
                self.rating_service.update_ratings_from_match(mid_fetched)
        if match_ids_missing_detail:
            update_query = "UPDATE live_matches SET status = 'missing_detail' WHERE match_id = ANY(:match_ids)"
            self.db.execute(update_query, {'match_ids': match_ids_missing_detail})
        logging.info(f"Successfully moved and cleared {len(match_ids_fetched) + len(match_ids_missing_detail)} matches.")

    def fetch_league_details(self, league_id):
        try:
            league_details = self.opendota_client.request(f'leagues/{league_id}')
            query = 'INSERT INTO league_details (id, "displayName", tier) VALUES (:league_id, :league_name, :tier)'
            params = {
                'league_id': league_details['leagueid'],
                'league_name': league_details['name'],
                'tier': str(league_details['tier']).upper()
            }
            self.league_cache[league_details['leagueid']] = {'league_name': league_details['name']}
            self.db.execute(query, params=params)
            return league_details['name']
        except Exception as e:
            logging.warning(f'Failed to fetch league details from OpenDota: {e}')
            return 'Unknown league'

    def run_forever(self, interval: float, max_interval: float, increment: float):
        while True:
            try:
                res = self.steam_api_client.request(interface='IDOTA2Match_570', endpoint='GetLiveLeagueGames/v1/')
                timestamp = datetime.now().timestamp()
                live_matches = res['result']['games']
                current_interval = interval
                self.process_cycle(live_matches, timestamp)
                time.sleep(interval)
            except Exception as e:
                logging.error(f"Live Monitor Error: {e}. cooling down for {current_interval}s")
                time.sleep(current_interval)
                current_interval = min(current_interval + increment, max_interval)

if __name__ == '__main__':
    db_manager = DatabaseManager()
    monitor = LiveMatchMonitor(
        db=db_manager, 
        draft_service=DraftService(db_manager),
        rating_system=RatingSystem(db_manager), 
        match_predictor=MatchPredictor(),
        steam_api_client=SteamApiClient(),
        opendota_client=OpenDotaClient()
    )
    monitor.run_forever(interval=15, max_interval=120, increment=15)