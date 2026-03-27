import threading
import time
import httpx
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

import logging
from basic_logger import setup_logger

from db_functions import DotaDB
setup_logger(logfile_path='logs/live-match-monitor.log')

class LiveMatchMonitor:
    def __init__(self, db: DotaDB):
        self.db = db
        self.logo_cache = {}

    def update_live_database(self):
        all_live = httpx.get("https://api.opendota.com/api/live").json()
        current_api_ids = []
        leagues = {row[0]: row[1] for row in self.db.query_select('SELECT id, "displayName" FROM league_details')}
        for m in all_live:
            league_id = m.get('league_id') 
            if league_id == 0 or not league_id: continue
            
            m_id = m['match_id']
            current_api_ids.append(m_id)

            league_name = leagues.get(league_id, 'Unknown League')
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
                game_time, radiant_lead, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (match_id) DO UPDATE SET
                    radiant_score = EXCLUDED.radiant_score,
                    radiant_logo = EXCLUDED.radiant_logo,
                    dire_logo = EXCLUDED.dire_logo,
                    dire_score = EXCLUDED.dire_score,
                    game_time = EXCLUDED.game_time,
                    radiant_lead = EXCLUDED.radiant_lead,
                    last_updated = CURRENT_TIMESTAMP;
            """
            params = (
                m_id, league_id, league_name, start_time, 
                m.get('team_id_radiant'), m.get('team_id_dire'),
                m.get('team_name_radiant', 'Radiant'), m.get('team_name_dire', 'Dire'),
                radiant_logo, dire_logo, m.get('radiant_score', 0), 
                m.get('dire_score', 0), m.get('game_time', 0), m.get('radiant_lead', 0)
            )
            self.db.query_execute(query, params=params)

        # CLEANUP: Delete matches that haven't been updated in the last 3 minutes
        # This handles games that finished or dropped off the API
        self.db.query_execute("DELETE FROM live_matches WHERE last_updated < NOW() - INTERVAL '3 minutes'")

    def get_team_logo(self, team_id, team_name):
        """Returns a URL. Fetches from DB or API if missing."""
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
            results = httpx.get(f"https://api.opendota.com/api/teams/{team_id}", timeout=10).json()
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