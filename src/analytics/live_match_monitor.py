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
from src.analytics import MatchFeatureExtractor
from cachetools import TTLCache
import joblib
logging.getLogger("httpx").setLevel(logging.WARNING)

class LiveMatchMonitor:
    def __init__(
        self, 
        db: DatabaseManager, 
        draft_service: DraftService, 
        rating_system: RatingSystem,
        match_predictor: MatchPredictor,
        steam_api_client: SteamApiClient,
        opendota_client: OpenDotaClient,
        feature_extractor: MatchFeatureExtractor
    ):
        self.db = db
        self.draft_service = draft_service
        self.rating_service = rating_system
        self.match_predictor = match_predictor
        self.league_cache = TTLCache(maxsize=100, ttl=3600)
        self.logo_cache = TTLCache(maxsize=500, ttl=86400)
        self.steam_api_client = steam_api_client
        self.opendota_client = opendota_client
        self.feature_extractor = feature_extractor

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
        if not live_matches:
            return
        self._sync_metadata(live_matches)

        matches_to_process = []

        for match in live_matches:
            match_id = match.get('match_id')
            league_id = match.get('league_id') 
            
            if league_id == 0 or not league_id or not match_id: 
                continue
            if not self.draft_service.draft_is_complete(match):
                continue
            if not match.get('radiant_team') or not match.get('dire_team'):
                continue 
            scoreboard = match.get('scoreboard')
            if not scoreboard:
                continue

            rad_players = [p for p in match.get('players', []) if p.get('team') == 0]
            dire_players = [p for p in match.get('players', []) if p.get('team') == 1]
            
            game_time = scoreboard.get('duration', 0)
            start_time = timestamp - game_time
            
            # TODO: move this to a cache as planned
            sub_patch, major_patch = self.opendota_client.get_internal_game_versions(int(round(start_time)), self.db) 

            matches_to_process.append({
                'match_id': match_id,
                'rad_heroes': [p['hero_id'] for p in rad_players],
                'dire_heroes': [p['hero_id'] for p in dire_players],
                'rad_players': [p['account_id'] for p in rad_players],
                'dire_players': [p['account_id'] for p in dire_players],
                'major_patch': major_patch,
                'sub_patch': sub_patch,
                'original_match': match,
                'start_time': start_time,
                'game_time': game_time
            })

        if not matches_to_process:
            return

        batch_draft_features = self.feature_extractor.batch_build_draft_features(matches_to_process, self.db)

        match_updates = []
        for params in matches_to_process:
            match_id = params['match_id']
            match = params['original_match']
            league_id = match.get('league_id')
            scoreboard = match.get('scoreboard')
            
            draft_features = batch_draft_features.get(match_id)
            if not draft_features:
                logging.warning(f'Draft features were excluded for match ID {match_id}')
                continue 

            rad_ratings = self.rating_service.get_ratings(params['rad_players'])
            dire_ratings = self.rating_service.get_ratings(params['dire_players'])
            rating_features = self.rating_service.calculate_rating_features(rad_ratings.values(), dire_ratings.values())
            
            feature_df = pd.DataFrame(draft_features | rating_features, index=[0])
            feature_df = feature_df.reindex(sorted(feature_df.columns), axis=1)
            

            rad_win_prob = float(self.match_predictor.predict_win_probability(feature_df)[0])
            draft_strength_rad, draft_strength_dire = self.feature_extractor.extract_pure_draft_strength(feature_df, self.match_predictor)
            
            players = match.get('players', [])
            rad_ordinal = self.rating_service.get_avg_team_ordinal(players, team=0, live=True)
            dire_ordinal = self.rating_service.get_avg_team_ordinal(players, team=1, live=True)

            rad_team = match.get('radiant_team', {})
            dire_team = match.get('dire_team', {})
            rad_id = int(rad_team.get('team_id') or 0)
            dire_id = int(dire_team.get('team_id') or 0)
            
            rad_score = scoreboard.get('radiant', {}).get('score', 0)
            dire_score = scoreboard.get('dire', {}).get('score', 0)
            
            league_name = self.league_cache.get(league_id, {}).get('league_name')
            if not league_name:
                league_name = self.fetch_league_details(league_id)
                
            rad_networth = np.array([p.get('net_worth', 0) for p in scoreboard.get('radiant', {}).get('players', [])])
            dire_networth = np.array([p.get('net_worth', 0) for p in scoreboard.get('dire', {}).get('players', [])])
            radiant_lead = np.sum(rad_networth) - np.sum(dire_networth)
            
            match_updates.append({
                'match_id': match_id,
                'league_id': league_id,
                'league_name': league_name or 'Unknown',
                'start_date_time': datetime.fromtimestamp(params['start_time']),
                'radiant_id': rad_id,
                'dire_id': dire_id,
                'radiant_name': rad_team.get('team_name', 'Radiant Unknown'),
                'dire_name': dire_team.get('team_name', 'Dire Unknown'),
                'radiant_logo': self.logo_cache.get(rad_id, {}).get('logo_url', ''),
                'dire_logo': self.logo_cache.get(dire_id, {}).get('logo_url', ''),
                'radiant_score': rad_score,
                'dire_score': dire_score,
                'game_time': int(round(params['game_time'])),
                'radiant_lead': radiant_lead,
                'is_finished': False, 
                'status': 'active',
                'radiant_draft_score': draft_strength_rad,
                'dire_draft_score': draft_strength_dire,
                'avg_radiant_rating': rad_ordinal,
                'avg_dire_rating': dire_ordinal,
                'rad_win_predicted': rad_win_prob,
                'last_updated': pd.Timestamp.now()
            })

        if match_updates:
            self.db.insert_df_into_table(
                pd.DataFrame(match_updates), 
                table_name="live_matches", 
                conflict_cols=["match_id"],
                avoid_cols=["start_date_time"]
            )
            logging.info('Successfully updated live_matches table')
        else:
            logging.info('No matches to be updated')

        ### Cleaning up inactive matches 
        query = """
            UPDATE live_matches 
            SET status = 'finished', is_finished = TRUE 
            WHERE status = 'active' 
                AND last_updated < NOW() - INTERVAL '15 minutes';
        """
        self.db.execute(query)

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
    rs = RatingSystem(db_manager)
    feature_extractor = MatchFeatureExtractor(rating_service=rs)
    monitor = LiveMatchMonitor(
        db=db_manager, 
        draft_service=DraftService(db_manager),
        rating_system=RatingSystem(db_manager), 
        match_predictor=MatchPredictor(),
        steam_api_client=SteamApiClient(),
        opendota_client=OpenDotaClient(),
        feature_extractor=feature_extractor
    )
    monitor.run_forever(interval=15, max_interval=120, increment=15)