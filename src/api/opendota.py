from .base import BaseDotaClient
from src.core.config import settings
import logging
import httpx
from ratelimit import limits, sleep_and_retry
from tenacity import retry, wait_exponential, retry_if_exception_type, stop_after_attempt
from datetime import datetime
from src.database import DatabaseManager
import time

class OpenDotaClient(BaseDotaClient):
    """
    Implementation of Dota Client for the OpenDota API.
    """
    OPENDOTA_URL = settings.opendota_url
    RUNE_MAP = {
        "0": "DOUBLE_DAMAGE",
        "1": "HASTE",
        "2": "ILLUSION",
        "3": "INVISIBILITY",
        "4": "REGEN",
        "5": "BOUNTY",
        "6": "ARCANE",
        "7": "WATER",
        "8": "WISDOM",
        "9": "SHIELD"
    }
    def __init__(self):
        self.client = httpx.Client()

    @retry(
        wait=wait_exponential(multiplier=10, min=10, max=100),
        stop=stop_after_attempt(2), #TODO Change this, API down
        retry=retry_if_exception_type((
            httpx.HTTPError,
            httpx.ConnectError, 
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.ReadError
        )),
        before_sleep=lambda retry_state: logging.warning(
            f"OpenDotaClient: Retry attempt {retry_state.attempt_number} after error: {retry_state.outcome.exception()}"
        ),
    )
    @sleep_and_retry 
    @limits(calls=60, period=60) #Minute
    @limits(calls=3000, period=86400) #Day
    def request(self, endpoint: str, method: str='GET'):
        if method == 'GET':
            response = self.client.get(f'{self.OPENDOTA_URL}/{endpoint}', timeout=30) 
        elif method == 'POST':
            response = self.client.post(f'{self.OPENDOTA_URL}/{endpoint}', timeout=30)
        else:
            raise ValueError('Unknown method passed')
        try:
            response.raise_for_status()
            result = response.json()
            return result
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logging.warning(f'Rate limit exceeded: retrying...')
                time.sleep(60)
                raise e
            if e.response.status_code == 404:
                logging.error(
                    f'''
                    HTTP error {e.response.status_code}: Wrong endpoint or data does not exist yet
                    for endpoint "{endpoint}"
                    '''
                )
            if e.response.status_code == 522:
                logging.error(
                    f'''
                    API server timeout for endpoint "{endpoint}"
                    '''
                )
                raise e
            logging.error(
                f"HTTP error {e.response.status_code} while requesting {e.request.url!r}: "
                f"{e.response.text}"
            )
        except Exception as e:
            logging.error(f"Failed {method} request at {self.OPENDOTA_URL}/{endpoint}") 
        
    def get_match(self, match_id, **kwargs):
        #TODO: refactor and optimize
        db_manager: DatabaseManager = kwargs.get('db_manager')
        match = self.request(f'matches/{match_id}')
        table_names = [
            'match_details', 'match_death_events', 'match_pick_bans', 'match_tower_deaths', 
            'match_players', 'match_purchases', 'match_runes', 'match_wards'
        ]
        storage = {table: [] for table in table_names}
        picks_bans = match.get('picks_bans', [])
        for mpb in picks_bans:
            storage['match_pick_bans'].append(
                {
                    'match_id': match_id,
                    'isPick': mpb['is_pick'],
                    'heroId': mpb['hero_id'],
                    'order': mpb['order'],
                    'isRadiant': mpb['team'] == 0
                }
            )
        start_timestamp = match['start_time']
        game_version = self.get_internal_game_versions(start_timestamp, db_manager)[0] # Stratz version ID 
        storage['match_details'] = {
            'id': match_id, 'tournamentId': match.get('tournament_id'), 'tournamentRound': match.get('tournament_round'),
            'leagueId': match['leagueid'], 'radiantTeamId': int(match.get('radiant_team_id', -1)), 'direTeamId': int(match.get('dire_team_id', -1)),
            'seriesId': match['series_id'], 'clusterId': match['cluster'], 'didRadiantWin': match['radiant_win'],
            'startDateTime': start_timestamp, 'endDateTime': match['start_time'] + match['duration'], 'durationSeconds': match['duration'],
            'firstBloodTime': match['first_blood_time'], 'towerStatusRadiant': match['tower_status_radiant'], 'towerStatusDire': match['tower_status_dire'],
            'barracksStatusRadiant': match['barracks_status_radiant'], 'barracksStatusDire': match['barracks_status_dire'], 'rank': match.get('rank_tier'),
            'actualRank': match.get('rank_tier_actual'), 'averageRank': match.get('average_rank'), 'averageImp': match.get('average_imp'),
            'radiant_score': match['radiant_score'], 'dire_score': match['dire_score'], 'gameVersionId': game_version
        }
        for obj in match.get('objectives'):
            if obj['type'] == 'building_kill':
                attacker = db_manager.get_hero_id_by_name(obj['unit'])
                if attacker == -1: #Hero ID defaulted to -1, it is an NPC
                    attacker = db_manager.get_npc_id_by_name(obj['unit'])
                    if attacker == -1:
                        logging.warning(f'Unknown ID found in objectives data for unit: {obj['unit']}')
                npc_id = db_manager.get_npc_id_by_name(obj['key'])
                if npc_id == -1:
                    logging.warning(f'Unknown ID found in data for NPC: {obj['key']}')
                storage['match_tower_deaths'].append(
                    {
                        'match_id': match_id,
                        'time': obj['time'],
                        'npcId': npc_id,
                        'isRadiant': 'goodguys' in obj['key'],
                        'attacker': attacker
                    }
                )
        for p in match['players']:
            hero_id = p['hero_id']
            for kill in p.get('kills_log'):
                killed_id = db_manager.get_hero_id_by_name(kill['key'])
                if killed_id == -1:
                    logging.warning(f'Unknown ID found in kill data for unit: {kill['key']}')
                storage['match_death_events'].append(
                    {
                        'match_id': match_id,
                        'hero_id': killed_id,
                        'time': kill['time'],
                        'attacker': hero_id
                    }
                )
            is_radiant = p['team_number'] == 0
            if (is_radiant and p['team_number'] == 0) or (not is_radiant and p['team_number'] == 1):
                is_victory = True
            else:
                is_victory = False       
            name = p.get('name')
            if name == '' or not name:
                name = 'Unknown'  
            storage['match_players'].append(
                {
                    'match_id': match_id,
                    'heroId': p['hero_id'],
                    'isRadiant': is_radiant,
                    'isVictory': is_victory,
                    'variant': p['hero_variant'],
                    'networth': p['net_worth'],
                    'goldPerMinute': p['gold_per_min'],
                    'goldSpent': p['gold_spent'],
                    'towerDamage': p['tower_damage'],
                    'heroDamage': p['hero_damage'],
                    'steamAccountId': p['account_id'],
                    'partyId': p['party_id'],
                    'name': name,
                    'kills': p['kills'],
                    'deaths': p['deaths'],
                    'assists': p.get('assists')
                }
            )
            for pur in p.get('purchase_log'):
                item_id = db_manager.get_item_id_by_name(pur['key'])
                if item_id == -1:
                    logging.warning(f'Unknown ID found in data for item: {pur['key']}')
                storage['match_purchases'].append(
                    {
                        'match_id': match_id,
                        'hero_id': hero_id,
                        'time': pur['time'],
                        'itemId': item_id
                    }
                )
            for rune in p.get('runes_log'):
                storage['match_runes'].append(
                    {
                        'match_id': match_id,
                        'hero_id': p['hero_id'],
                        'time': rune['time'],
                        'rune': self.RUNE_MAP[rune['key']]
                    }
                )
            for ward in p.get('obs_log'):
                storage['match_wards'].append(
                    {
                        'match_id': match_id,
                        'hero_id': p['hero_id'],
                        'time': ward['time'],
                        'type': 0,
                        'positionX': ward['x'],
                        'positionY': ward['y']
                    }
                )
            for ward in p.get('sen_log'):
                storage['match_wards'].append(
                    {
                        'match_id': match_id,
                        'hero_id': p['hero_id'],
                        'time': ward['time'],
                        'type': 1,
                        'positionX': ward['x'],
                        'positionY': ward['y']
                    }
                )  
        return storage
        
    def is_parsed_match(self, **kwargs):
        match_id = kwargs.get('match_id')
        job_id = kwargs.get('job_id')
        if match_id:
            try:
                response = self.client.get(f'{self.OPENDOTA_URL}/matches/{match_id}')
                if response.status_code == 200:
                    return True
                return False
            except Exception as e:
                logging.warning(f'Failed to check match {match_id} parsing status: {e}')
                return False

        elif job_id:
            try:
                response = self.client.get(f'{self.OPENDOTA_URL}/request/{job_id}')
                response.raise_for_status()
                result = response.json()
                if not result:
                    return True
                else: 
                    return False
            except Exception as e:
                logging.error(f'Error with response: {e}')
                return False
        
    def request_parse(self, match_id: int) -> int:
        job_id = self.request(f'request/{match_id}', method='POST')['job']['jobId']
        if isinstance(job_id, int):
            return job_id
        else:
            logging.warning(f'API did not return expected job ID')
        
    def get_internal_game_versions(self, start_timestamp: int, db_manager: DatabaseManager):
        """
        Fetches the Stratz and OpenDota game version IDs 
        from an Unix timestamp relating to the start of the game.
        Stratz separates patch IDs between sub-patches, OpenDota
        doesn't, this is useful for sub-meta analysis.
        Returns a tuple (stratz_patch_id, opendota_patch_id)
        """
        start_datetime = datetime.fromtimestamp(start_timestamp)
        query = 'SELECT id, opendota_patch_id FROM patches WHERE "asOfDateTime" < :start_datetime ORDER BY "asOfDateTime" DESC LIMIT 1'
        game_versions = db_manager.select(query, params={'start_datetime': start_datetime})[0]
        return game_versions