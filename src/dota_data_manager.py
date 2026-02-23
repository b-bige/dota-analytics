import os
import sys
sys.path.append(os.path.abspath('./src'))

from db_functions import DotaDB

import logging
import basic_logger
basic_logger.setup_logger()

## TODO: make it a dataclass
class DotaDataManager:
    def __init__(self, db):
        self.db = db
        self._load_reference_data()
    
    def _load_reference_data(self):
        self.main_leagues = self._get_main_leagues(self.db)
        self.dreamleague_leagues = self._get_dreamleague_leagues(self.db)

    def _get_main_leagues(self, db):
        queries = [
            'SELECT id FROM league_details ld WHERE ld."displayName" LIKE \'ESL%\' AND ld."prizePool" <> 0;',
            'SELECT id FROM league_details ld WHERE ld."displayName" LIKE \'%DreamLeague%\' AND ld."prizePool" <> 0;',
            'SELECT id FROM league_details ld WHERE ld."displayName" LIKE \'%International%\' AND ld."prizePool" <> 0;',
            'SELECT id FROM league_details ld WHERE ld."displayName" LIKE \'FISSURE%\' AND ld."displayName" NOT LIKE \'%Special\' AND ld."prizePool" <> 0;',
            'SELECT id FROM league_details ld WHERE ld."displayName" LIKE \'%Clavision%\' AND ld."prizePool" <> 0;'
        ]
        league_ids = []
        for query in queries:
            for lid in [res[0] for res in db.query_select(query)]:
                league_ids.append(lid)
        return league_ids
    
    def _get_dreamleague_leagues(self, db):
        leagues = []
        for league in db.query_opendota(endpoint='leagues'):
            if 'DreamLeague' in league['name']:
                leagues.append({'id': league['leagueid'], 'name': league['name']})
        return leagues