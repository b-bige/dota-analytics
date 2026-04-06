import threading
import time
import httpx
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

import logging

from db_functions import DotaDB

class LiveMatchMonitor:
    def __init__(self, db: DotaDB):
        self.db = db
        self.logo_cache = {}
        self.httpx_client = httpx.Client()

    def update_live_database(self):
        all_live = self.db.query_opendota(self.httpx_client, 'live')
        current_api_ids = []
        leagues = {row[0]: row[1] for row in self.db.query_select('SELECT id, "displayName" FROM league_details')}
        for m in all_live:
            league_id = m.get('league_id') 
            if league_id == 0 or not league_id: continue
            is_finished = m.get('deactivate_time') != 0 
            
            m_id = m['match_id']
            current_api_ids.append(m_id)
            league_name = leagues.get(league_id, None)
            if not league_name:
                league_name = self.get_league_details(league_id)
            start_time = datetime.fromtimestamp(m.get('activate_time'))
            r_id = int(m.get('team_id_radiant')) or 0
            d_id = int(m.get('team_id_dire')) or 0
            radiant_logo = self.get_team_logo(r_id, m.get('team_name_radiant'))
            dire_logo = self.get_team_logo(d_id, m.get('team_name_dire'))
            query = """
                INSERT INTO live_matches (match_id, league_id, league_name, 
                start_date_time, radiant_id, dire_id, 
                radiant_name, dire_name, 
                radiant_logo, dire_logo, radiant_score, dire_score, 
                game_time, radiant_lead, is_finished, status, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (match_id) DO UPDATE SET
                    league_name = EXCLUDED.league_name,
                    radiant_score = EXCLUDED.radiant_score,
                    radiant_logo = EXCLUDED.radiant_logo,
                    dire_logo = EXCLUDED.dire_logo,
                    dire_score = EXCLUDED.dire_score,
                    game_time = EXCLUDED.game_time,
                    radiant_lead = EXCLUDED.radiant_lead,
                    is_finished = EXCLUDED.is_finished,
                    last_updated = CURRENT_TIMESTAMP
                WHERE live_matches.game_time IS DISTINCT FROM EXCLUDED.game_time;
            """
            params = (
                m_id, league_id, league_name, start_time, 
                m.get('team_id_radiant'), m.get('team_id_dire'),
                m.get('team_name_radiant', 'Radiant'), m.get('team_name_dire', 'Dire'),
                radiant_logo, dire_logo, m.get('radiant_score', 0), 
                m.get('dire_score', 0), m.get('game_time', 0), m.get('radiant_lead', 0),
                is_finished, 'active'
            )
            self.db.query_execute(query, params=params)

        # CLEANUP: See if match is parsed yet on opendota, if not then request it and wait, 
        # save the details and drop the matches
        self.handle_finished()

    def handle_finished(self):
        """Requests parsing if not yet parsed on idle or deactivated live matches and stores them in the database"""
        query = """
        SELECT match_id FROM live_matches WHERE last_updated < NOW() - INTERVAL '15 minutes' AND status = 'active' 
        UNION
        SELECT match_id FROM live_matches WHERE (last_updated < NOW() - INTERVAL '10 minutes') AND is_finished AND status = 'active'
        """
        active_ids = [r[0] for r in self.db.query_select(query)]  
        query = "SELECT match_id FROM live_matches WHERE status = 'pending_parse'"
        pending_ids = [r[0] for r in self.db.query_select(query)]
        for mid in active_ids:
            try:
                self.db.fetch_match_opendota(self.httpx_client, mid)
                self.db.query_execute('DELETE FROM live_matches WHERE match_id = %s', (mid, ))
            except:
                self.db.request_parse_opendota(self.httpx_client, mid)
                self.db.query_execute("UPDATE live_matches SET stauts = 'pending_parse' WHERE match_id = %s", (mid, ))
        for mid in pending_ids:
            if self.db.is_match_parsed_opendota(self.httpx_client, mid):
                self.db.fetch_match_opendota(self.httpx_client, mid)
                self.db.query_execute('DELETE FROM live_matches WHERE match_id = %s', (mid, ))

    def get_league_details(self, league_id):
        """Returns league name. Fetches from API and saves the details after to the db."""
        result = self.db.query_opendota(self.httpx_client, f'leagues/{league_id}')
        if result:
            try:
                query = 'INSERT INTO league_details (id, "displayName", tier) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING'
                self.db.query_execute(query, params=(result['leagueid'], result['name'], str(result['tier']).upper()))
                return result['name']
            except Exception as e:
                logging.error(f'Failed to fetch league details: {e}')
        return 'Unknown League'

    def get_team_logo(self, team_id, team_name):
        """Returns a URL. Fetches from DB or API if missing, and saves the data."""
        if not team_id or team_id == 0:
            return '/assets/no_image.svg'
        
        if team_id in self.logo_cache:
            return self.logo_cache[team_id]
        db_row = self.db.query_select("SELECT logo_url FROM team_logos WHERE team_id = %s", params=(team_id,))
        if db_row:
            url = db_row[0][0]
            self.logo_cache[team_id] = url
            return url
        try:
            logging.info(f"Fetching logo for new team: {team_name} ({team_id})")
            results = self.db.query_opendota(self.httpx_client, f'teams/{team_id}')
            url = results.get("logo_url") or "/assets/no_image.svg"
            
            # Save to DB so we have it for next time
            self.db.query_execute(
                "INSERT INTO team_logos (team_id, logo_url) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                params=(team_id, url)
            )
            self.logo_cache[team_id] = url
            return url
        except Exception as e:
            logging.error(f"Failed to fetch team logo: {e}")
            return "/assets/no_image.svg"

    def run_forever(self, interval=60):
        while True:
            try:
                self.update_live_database()
            except Exception as e:
                logging.error(f"Live Monitor Error: {e}")
            time.sleep(interval)

monitor = LiveMatchMonitor(DotaDB())