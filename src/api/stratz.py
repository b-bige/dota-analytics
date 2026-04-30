from .base import BaseDotaClient
from .stratz_queries import MATCH_IS_PARSED, MATCH_DETAIL_QUERY
from src.core.config import settings
import logging
import httpx
from ratelimit import limits, sleep_and_retry
from tenacity import retry, wait_exponential, retry_if_exception_type

class StratzClient(BaseDotaClient):
    """
    Implementation of Dota Client for the stratz API.
    """
    STRATZ_HEADERS = {
            'User-Agent': 'STRATZ_API',
            "Authorization": f"Bearer {settings.stratz_api_key}"
        }
    STRATZ_URL = settings.stratz_url
    TABLE_MAP = {
        'details': 'match_details', 'pickBans': 'match_pick_bans', 'chatEvents': 'match_chat_events',
        'predictedWinRates': 'match_predicted_win_rates', 'winRates': 'match_win_rates', 
        'leads': 'match_leads', 'kills': 'match_kills', 'towerDeaths': 'match_tower_deaths', 'towerStatus': 'match_tower_updates', 
        'snapshots': 'match_snapshots', 'outposts': 'match_outpost_updates', 'players': 'match_players', 
        'impPerMinute': 'match_imp_per_minute', 'performanceMetrics': 'match_performance_metrics', 
        'locationReport': 'match_position', 'deathEvents': 'match_death_events', 'farmDistributionReport': 'match_farm', 
        'itemPurchases': 'match_purchases', 'courierKills': 'match_courier_kills', 'runes': 'match_runes',
        'wards': 'match_wards', 'wardDestruction': 'match_ward_destructions'
    }
    def __init__(self):
        self.client = httpx.Client(headers=self.STRATZ_HEADERS)

    @retry(
        wait=wait_exponential(multiplier=30, min=30, max=500),
        retry=retry_if_exception_type((
            KeyError,
            httpx.HTTPError,
            httpx.ConnectError, 
            httpx.ConnectTimeout,
        )),
        before_sleep=lambda retry_state: logging.warning(
            f"StratzClient: Retry attempt {retry_state.attempt_number} after error: {retry_state.outcome.exception()}"
        ),
    )
    @sleep_and_retry 
    @limits(calls=20, period=1) #Second
    @limits(calls=200, period=60) #Minute
    @limits(calls=2000, period=3600) #Hour 
    @limits(calls=10000, period=86400) #Day
    def request(self, query: str, variables: dict={}):
        response = self.client.post(
            url=self.STRATZ_URL,
            json={'query': query, 'variables': variables}
        )
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            raise Exception(f"GraphQL Error: {result['errors']}")
        if "data" not in result:
            raise KeyError(f"No data in result, probably rate limit exceeded: {result}")
        return result

    def get_match(self, match_id):
        storage = {key: [] for key in self.TABLE_MAP.keys()}
        match = self.request(query=MATCH_DETAIL_QUERY, variables={'id': match_id})
        if not match:
            logging.warning(f"There was no match data for match ID {match_id} at Stratz")
            return None
        match_details = {}
        for key, value in match.items():
            if type(value) != list and value is not None:
                match_details[key] = value
        storage['details'].append(match_details)

        pb = match.get('pickBans', [])
        if pb:
            for entry in pb: 
                entry['match_id'] = match_id
            storage['pickBans'].extend(pb)
        else:
            pass
        ce = match.get('chatEvents', [])
        if ce:
            for entry in ce:
                entry['match_id'] = match_id
            storage['chatEvents'].extend(ce)
        else:
            pass
        try:
            storage['winRates'].extend([
                {
                    'match_id': match_id, 
                    'minute': minute, 
                    'win_rates': rate
                }
                for minute, rate in enumerate(match['winRates'])
            ])
        except:
            pass
        try:
            storage['predictedWinRates'].extend([
                {
                    'match_id': match_id, 
                    'minute': minute, 
                    'predicted_win_rate': rate
                }
                for minute, rate in enumerate(match['predictedWinRates'])
            ])
        except:
            pass
        try:
            storage['leads'].extend([
                {
                    'match_id': match_id,
                    'minute': minute,
                    'radiantNetworthLeads': rnwl,
                    'radiantExperienceLeads': rel,
                }
                for minute, (rnwl, rel) in enumerate(zip(match['radiantNetworthLeads'], match['radiantExperienceLeads']))
            ])
        except:
            pass
        try:
            storage['kills'].extend([
                {
                    'match_id': match_id,
                    'minute': minute,
                    'radiantKills': rk,
                    'direKills': dk
                }
                for minute, (rk, dk) in enumerate(zip(match['radiantKills'], match['direKills']))
            ])
        except:
            pass
        td = match.get('towerDeaths', [])
        if td:
            for entry in td:
                entry['match_id'] = match_id
            storage['towerDeaths'].extend(td)
        else:
            pass

        snapshots = []
        tower_updates = []
        outpost_updates = []
        tower_status = match.get('towerStatus', [])
        if tower_status:
            for index, buildings in enumerate(match['towerStatus']):
                snapshot_id = str(match['id']) + f'_{index}'
                snapshots.append(
                {
                    'snapshot_id': snapshot_id,
                    'match_id': match['id'],
                    'order_index': index
                })

                towers = buildings['towers'] 
                for entry in towers:
                    entry['snapshot_id'] = snapshot_id
                tower_updates.extend(towers)

                outposts = buildings['outposts'] 
                for entry in outposts:
                    entry['snapshot_id'] = snapshot_id
                outpost_updates.extend(outposts)
            storage['snapshots'].extend(snapshots)
            storage['towerStatus'].extend(tower_updates)
            storage['outposts'].extend(outpost_updates)
        for idx, player in enumerate(match['players']):
            try:
                hero_id = player['heroId']
                player_row = {'match_id': match_id}
                stats = player['stats']
                for key, value in player.items():
                    if key == 'stats':
                        continue
                    if key == 'steamAccount' and isinstance(value, dict):
                        for sa_key, sa_value in value.items():
                            if sa_key == 'proSteamAccount' and isinstance(sa_value, dict):
                                player_row['proSteamAccount_teamId'] = sa_value['teamId']
                                player_row['proSteamAccount_name'] = sa_value['name']
                    else:
                        player_row[key] = value
                storage['players'].append(player_row)
            except:
                logging.warning('Failed to fetch basic player stats')
            try:
                storage['impPerMinute'].extend([
                    {
                        'match_id': match_id,
                        'hero_id': hero_id,
                        'minute': minute,
                        'imp_per_minute': imp
                    }
                    for minute, imp in enumerate(stats['impPerMinute']) 
                ])
            except:
                pass
            try:
                storage['performanceMetrics'].extend([
                    {
                        'match_id': match_id,
                        'hero_id': hero_id,
                        'minute': minute,
                        'gold_per_minute': gpm,
                        'networth_per_minute': nwpm,
                        'experience_per_minute': exp,
                        'tower_damage_per_minute': tdpm,
                        'camp_stack': camp_stack
                    }
                    for minute, (gpm, nwpm, exp, tdpm, camp_stack) in enumerate(zip(
                        stats['goldPerMinute'], stats['networthPerMinute'], 
                        stats['experiencePerMinute'], stats['towerDamagePerMinute'],
                        stats['campStack']
                    ))
                ])
            except:
                pass
            try:
                for source_type, value in stats.get('farmDistributionReport', {}).items():
                    if source_type != 'buyBackGold':
                        items = [value] if isinstance(value, dict) else value
                        if items:
                            storage['farmDistributionReport'].extend([
                                {
                                    'match_id': match_id,
                                    'hero_id': hero_id,
                                    'source_type': source_type, 
                                    'id': v['id'],
                                    'gold': v['gold']
                                }
                                for v in items
                        ])
                    else:
                        storage['farmDistributionReport'].append({
                            'match_id': match_id,
                            'hero_id': hero_id,
                            'source_type': source_type, 
                            'id': -1,
                            'gold': value
                        })
            except:
                pass
            try:
                pos_x = [px['positionX'] for px in stats['locationReport']]
                pos_y = [py['positionY'] for py in stats['locationReport']]
                storage['locationReport'].extend([
                    {
                        'match_id': match_id,
                        'hero_id': hero_id,
                        'minute': minute,
                        'position_x': pos_x,
                        'position_y': pos_y
                    }
                    for minute, (pos_x, pos_y) in enumerate(zip(pos_x, pos_y))
                ])
            except:
                pass
            for hero_stat in ['deathEvents', 'itemPurchases', 'courierKills', 'runes', 'wards', 'wardDestruction']:
                hs = stats[hero_stat]
                if hs:
                    for entry in hs:
                        entry['match_id'] = match_id
                        entry['hero_id'] = hero_id
                    storage[hero_stat].extend(hs)
        return storage
        
    def is_parsed_match(self, **kwargs):
        match_id = kwargs.get('match_id')
        if not match_id:
            raise ValueError("Stratz requires match_id to check status")
        
        match = self.request(MATCH_IS_PARSED, variables={'id': match_id})['data']['match']
        if not match:
            logging.info(f'No match data yet for ID {match_id} at Stratz')
            return False
        parsed_timestamp = match.get('parsedDateTime', None)
        if not parsed_timestamp:
            logging.info(f'Match not parsed yet for {match_id} at Stratz')
            return False
        return True