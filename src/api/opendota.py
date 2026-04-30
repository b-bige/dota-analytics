from .base import BaseDotaClient
from src.core.config import settings
import logging
import httpx
from ratelimit import limits, sleep_and_retry
from tenacity import retry, wait_exponential, retry_if_exception_type
from datetime import datetime
from src.database import DatabaseManager

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
        retry=retry_if_exception_type((
            httpx.HTTPError,
            httpx.ConnectError, 
            httpx.ConnectTimeout,
        )),
        before_sleep=lambda retry_state: logging.warning(
            f"OpenDotaClient: Retry attempt {retry_state.attempt_number} after error: {retry_state.outcome.exception()}"
        ),
    )
    @sleep_and_retry 
    @limits(calls=60, period=60) #Minute
    @limits(calls=3000, period=86400) #Day
    def request(self, endpoint: str):
        response = self.client.get(f'{self.OPENDOTA_URL}/{endpoint}') 
        try:
            response.raise_for_status()
            result = response.json()
            return result
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logging.warning(f'Rate limit exceeded: retrying...')
                raise httpx.HTTPStatusError
            logging.error(
                f"HTTP error {e.response.status_code} while requesting {e.request.url!r}: "
                f"{e.response.text}"
            )
        except Exception as e:
            logging.error(f"Failed GET request at {self.OPENDOTA_URL}/{endpoint}")
        
    def get_match(self, match_id, **kwargs):
        #TODO: refactor and optimize
        db_manager = kwargs.get('db_manager')
        match = self.client.get(f'{self.OPENDOTA_URL}/matches/{match_id}')
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
        game_version = self.get_internal_game_version(start_timestamp, db_manager)
        storage['match_details'] = {
            'id': match_id, 'tournamentId': match.get('tournament_id'), 'tournamentRound': match.get('tournament_round'),
            'leagueId': match['leagueid'], 'radiantTeamId': match.get('radiant_team_id'), 'direTeamId': match.get('dire_team_id'),
            'seriesId': match['series_id'], 'clusterId': match['cluster'], 'didRadiantWin': match['radiant_win'],
            'startDateTime': start_timestamp, 'endDateTime': match['start_time'] + match['duration'], 'durationSeconds': match['duration'],
            'firstBloodTime': match['first_blood_time'], 'towerStatusRadiant': match['tower_status_radiant'], 'towerStatusDire': match['tower_status_dire'],
            'barracksStatusRadiant': match['barracks_status_radiant'], 'barracksStatusDire': match['barracks_status_dire'], 'rank': match.get('rank_tier'),
            'actualRank': match.get('rank_tier_actual'), 'averageRank': match.get('average_rank'), 'averageImp': match.get('average_imp'),
            'radiant_score': match['radiant_score'], 'dire_score': match['dire_score'], 'gameVersionId': game_version
        }
        for obj in match.get('objectives'):
            if obj['type'] == 'building_kill':
                try:
                    attacker = self.heroes[self.heroes['name'] == obj['unit']].get('id').iloc[0]
                except:
                    attacker = 'non-hero'
                storage['match_tower_deaths'].append(
                    {
                        'match_id': match_id,
                        'time': obj['time'],
                        'npcId': self.npcs[self.npcs['name'] == obj['key']].get('id').iloc[0],
                        'isRadiant': 'goodguys' in obj['key'],
                        'attacker': attacker
                    }
                )
        for p in match['players']:
            hero_id = p['hero_id']
            for kill in p.get('kills_log'):
                try: 
                    killed_id = int(self.heroes[self.heroes['name'] == kill['key']].get('id').iloc[0])
                except:
                    killed_id = -1
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
                    'name': p['name'],
                    'kills': p['kills'],
                    'deaths': p['deaths'],
                    'assists': p['assists']
                }
            )
            for pur in p.get('purchase_log'):
                storage['match_purchases'].append(
                    {
                        'match_id': match_id,
                        'hero_id': hero_id,
                        'time': pur['time'],
                        'itemId': self.items[self.items['shortName'] == pur['key']].get('id').iloc[0]
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
        job_id = kwargs.get('job_id')
        if not job_id:
            raise ValueError("OpenDota requires job_id to check status")
        
        response = self.client.get(f'{self.OPENDOTA_URL}/request/{job_id}')
        try:
            response.raise_for_status()
            result = response.json()
            if not result:
                return True
            else: 
                return False
        except Exception as e:
            logging.error(f'Error with response: {e}')
            return False
        
    def get_internal_game_version(self, start_timestamp: int, db_manager: DatabaseManager):
        """
        Fetches the Internal/Stratz-matching game version ID 
        from an Unix timestamp relating to the start of the game.
        """
        start_datetime = datetime.fromtimestamp(start_timestamp)
        query = 'SELECT id FROM patches WHERE "asOfDateTime" < :start_datetime LIMIT 1'
        game_version = db_manager.select(query, params={'start_datetime': start_datetime})[0]
        return game_version
    
odc = OpenDotaClient()
odc.get_match()