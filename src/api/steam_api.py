from .base import BaseDotaClient
from src.core.config import settings
import logging
import httpx
from ratelimit import limits, sleep_and_retry
from tenacity import retry, wait_exponential, retry_if_exception_type, stop_after_attempt
from datetime import datetime
from src.database import DatabaseManager
import time
import json

class SteamApiClient(BaseDotaClient):
    """
    Implementation of Dota Client for the Steam Web API.
    """
    STEAM_WEB_API_URL = settings.steam_web_api_url
    def __init__(self):
        self.api_key = settings.steam_web_api_key
        self.client = httpx.Client()

    def request(self, interface, endpoint, method: str = 'GET'):
        params = {'key': self.api_key}
        url = f'{self.STEAM_WEB_API_URL}/{interface}/{endpoint}'
        #TODO: implement error handling for all possibilities
        if method == 'GET':
            try:
                response = self.client.get(url, params=params, timeout=30)
                response.raise_for_status()

                raw_bytes = response.content
                clean_text = raw_bytes.decode('utf-8', errors='replace')
                data = json.loads(clean_text)
                #TODO: move back logging to the httpx library, sanitize logging
                logging.info(f'HTTP Requests: GET {self.STEAM_WEB_API_URL}/{interface}/{endpoint}?key=API_KEY "HTTP/1.1 200 OK"')
                return data
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logging.warning(f'Rate limit exceeded: retrying...')
                    time.sleep(60)
                    raise e
                if e.response.status_code == 404:
                    logging.error(
                        f'''
                        HTTP error {e.response.status_code}: Endpoint does not exist
                        for endpoint "{interface}/{endpoint}"
                        '''
                    )
                    raise e
                if e.response.status_code == 405:
                    logging.error(
                        f'''
                        HTTP error {e.response.status_code}: Method not allowed for endpoint "{interface}/{endpoint}"    
                        '''
                    )
                if e.response.status_code == 522:
                    logging.error(
                        f'''
                        API server timeout for endpoint "{interface}/{endpoint}"
                        '''
                    )
                    raise e
                logging.error(
                    f"HTTP error {e.response.status_code} while requesting {e.request.url!r}: "
                    f"{e.response.text}"
                )
        
    #NOTE: Steam Web Api is quite complex, so OpenDota and Stratz will serve us better here for now.
    def get_match(self, match_id: int):
        pass

    def is_parsed_match(self, **kwargs):
        pass
