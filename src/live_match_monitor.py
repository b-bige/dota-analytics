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
            # UPSERT: Insert or update if exists
            query = """
                INSERT INTO live_matches 
                (match_id, league_id, league_name, 
                start_date_time, radiant_name, dire_name, 
                radiant_logo, dire_logo, radiant_score, dire_score, 
                game_time, radiant_lead, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (match_id) DO UPDATE SET
                    radiant_score = EXCLUDED.radiant_score,
                    dire_score = EXCLUDED.dire_score,
                    game_time = EXCLUDED.game_time,
                    radiant_lead = EXCLUDED.radiant_lead,
                    last_updated = CURRENT_TIMESTAMP;
            """
            self.db.query_execute(query, params=(
                m_id, league_id, league_name, start_time, m.get('team_name_radiant', 'Radiant'), m.get('team_name_dire', 'Dire'),
                str(m.get('team_logo_radiant')), str(m.get('team_logo_dire')), m.get('radiant_score', 0), 
                m.get('dire_score', 0), m.get('game_time', 0), m.get('radiant_lead', 0)
            ))

        # CLEANUP: Delete matches that haven't been updated in the last 3 minutes
        # This handles games that finished or dropped off the API
        self.db.query_execute("DELETE FROM live_matches WHERE last_updated < NOW() - INTERVAL '3 minutes'")

    def run_forever(self, interval=60):
        while True:
            try:
                self.update_live_database()
            except Exception as e:
                logging.error(f"Live Monitor Error: {e}")
            time.sleep(interval)

monitor = LiveMatchMonitor(DotaDB())