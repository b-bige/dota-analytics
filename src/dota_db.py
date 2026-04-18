import pandas as pd 
import psycopg
from psycopg.types.json import Jsonb
from psycopg import sql
import httpx
import time
import os
from dotenv import load_dotenv
import logging
from ratelimit import limits, sleep_and_retry
from tenacity import retry, wait_exponential, retry_if_exception_type

class DotaDB:
    def __init__(self, schema: str='public', local: bool = False):
        self.set_local_or_remote(schema=schema, local=local)
        query = 'SELECT * FROM hero_details'
        self.heroes = self.select_to_df(query, table='hero_details') ##TODO
        query = 'SELECT * FROM item_details_opendota' 
        self.items = self.select_to_df(query, table='item_details_opendota') ##TODO
        query = 'SELECT * FROM npcs'
        self.npcs = self.select_to_df(query, table='npcs') ##TODO

    def set_local_or_remote(self, schema:str='public', local=False):
        load_dotenv()
        user = os.getenv("DB_USER")
        port = os.getenv("DB_PORT")
        dbname = os.getenv("DB_NAME")
        if local:
            host = os.getenv("DB_LOCAL_HOST")
            password = os.getenv("DB_LOCAL_PASSWORD")
        else:
            host = os.getenv("DB_HOST")
            password = os.getenv("DB_PASSWORD")
        
        self.conn_str = f"postgresql://{user}:{password}@{host}:{port}/{dbname}?options=-csearch_path%3D{schema}"
        self.stratz_api_key = os.getenv("API_KEY")
        self.stratz_url = 'https://api.stratz.com/graphql'
        self.stratz_headers = {
            'User-Agent': 'STRATZ_API',
            "Authorization": f"Bearer {self.stratz_api_key}"
        }
        self.opendota_url = 'https://api.opendota.com/api'

    def set_schema(self, schema: str='public'):
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        dbname = os.getenv("DB_NAME")
        self.conn_str = f"postgresql://{user}:{password}@{host}:{port}/{dbname}?options=-csearch_path%3D{schema}"

    def select(self, query, params=None, identifiers=None):
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                if identifiers:
                    final_query = sql.SQL(query).format(*[sql.Identifier(name) for name in identifiers])
                else:
                    final_query = sql.SQL(query)
                cur.execute(final_query, params)
                return cur.fetchall() if cur.description else None
            
    def select_to_df(self, query, columns=None, params=None, identifiers=None, table=None):
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                if identifiers:
                    final_query = sql.SQL(query).format(*[sql.Identifier(name) for name in identifiers])
                else:
                    final_query = sql.SQL(query)
                cur.execute(final_query, params)
                
                if cur.description:
                    data = cur.fetchall()
                    if columns: 
                        return pd.DataFrame(data, columns=columns)
                    else:
                        table_query = "SELECT COLUMN_NAME FROM information_schema.columns WHERE table_name = %s"
                        table_columns = [c[0] for c in self.select(table_query, params=(table, ))]
                        return pd.DataFrame(data, columns=table_columns)
                return None
            
    def create_table_from_df(self, df, table_name, convert_dtypes=True, add_serial_id=False, jsonb_cols=[]):
        if convert_dtypes:
            schema_df = df.convert_dtypes()
        else:
            schema_df = df
        try:
            with psycopg.connect(self.conn_str) as conn:
                cols = []
                primary_key_assigned = False
                if add_serial_id:
                    schema_df.insert(0, 'id', range(len(schema_df)))
                for col_name, dtype in zip(schema_df.columns, schema_df.dtypes):
                    if col_name in jsonb_cols:
                        continue
                    if 'id' in col_name.lower() and not primary_key_assigned:
                        pg_type = "BIGSERIAL"
                        cols.append(f'"{col_name}" {pg_type} PRIMARY KEY')
                        primary_key_assigned = True
                    else:
                        pg_type = self.get_pg_type(dtype)
                        cols.append(f'"{col_name}" {pg_type}')
                for col_name in jsonb_cols:
                    cols.append(f'"{col_name}" JSONB')
                
                schema = ", ".join(cols)
                create_table_query = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({schema});'
                with conn.cursor() as cur:
                    cur.execute(create_table_query)
                if primary_key_assigned:
                    conn.commit()
                else:
                    raise KeyError
        except Exception as e:
            logging.error(f"Error creating table '{table_name}': {e}")
            return
        logging.info(f"Table '{table_name}' created successfully.")

    def insert_df_into_table(self, df, table_name, conflict_cols=[], update_cols=None, jsonb_cols=[]):
        if df.empty:
            return

        df = df.convert_dtypes()
        clean_df = df.astype(object).where(pd.notnull(df), None)
        
        for col in jsonb_cols:
            if col in clean_df.columns:
                clean_df[col] = clean_df[col].apply(lambda x: Jsonb(x) if x is not None else None)

        col_names = [f'"{c}"' for c in clean_df.columns]
        col_names_str = ", ".join(col_names)
        
        upsert_clause = ""
        if conflict_cols:
            if update_cols is None:
                update_cols = [c for c in clean_df.columns if c not in conflict_cols]
            
            update_stmt = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in update_cols])
            conflict_target = ", ".join([f'"{c}"' for c in conflict_cols])
            upsert_clause = f"ON CONFLICT ({conflict_target}) DO UPDATE SET {update_stmt}"

        try:
            with psycopg.connect(self.conn_str) as conn:
                with conn.cursor() as cur:
                    cur.execute(f'CREATE TEMP TABLE staging_table AS SELECT * FROM "{table_name}" LIMIT 0')

                    copy_query = f'COPY staging_table ({col_names_str}) FROM STDIN'
                    with cur.copy(copy_query) as copy:
                        for row in clean_df.itertuples(index=False):
                            copy.write_row(row)

                    final_query = f"""
                        INSERT INTO "{table_name}" ({col_names_str})
                        SELECT {col_names_str} FROM staging_table
                        {upsert_clause}
                    """
                    cur.execute(final_query)

            mode = "Upserted" if conflict_cols else "Inserted"
            logging.info(f"{mode} {len(clean_df)} rows into '{table_name}' successfully.")
            
        except Exception as e:
            logging.error(f"Error processing data for table '{table_name}': {e}")

    def query_execute(self, query, params=None, identifiers=None):
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                if identifiers:
                    final_query = sql.SQL(query).format(*[sql.Identifier(name) for name in identifiers])
                else:
                    final_query = sql.SQL(query)
                cur.execute(final_query, params)
                conn.commit()
                return None
            
    def query_executemany(self, query, params=None, identifiers=None):
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                if identifiers:
                    final_query = sql.SQL(query).format(*[sql.Identifier(name) for name in identifiers])
                else:
                    final_query = sql.SQL(query)
                try:
                    cur.executemany(final_query, params)
                    conn.commit()
                    logging.info('Successfully executed query')
                except Exception as e:
                    logging.error(f'Failed to execute query: {e}')
                return None

    @retry(
        wait=wait_exponential(multiplier=30, min=30, max=500),
        retry=retry_if_exception_type((
            KeyError,
            httpx.HTTPError,
            httpx.ConnectError, 
            httpx.ConnectTimeout,
        )),
        before_sleep=lambda retry_state: logging.warning(
            f"Retry attempt {retry_state.attempt_number} after error: {retry_state.outcome.exception()}"
        ),
    )
    @sleep_and_retry 
    @limits(calls=20, period=1)
    @limits(calls=200, period=60)
    @limits(calls=2000, period=3600)
    @limits(calls=10000, period=86400)
    def fetch_stratz(self, client: httpx.Client, query: str, variables:dict={}):
        response = client.post(
            url=self.stratz_url,
            json={'query': query, 'variables': variables}
        )
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            raise Exception(f"GraphQL Error: {result['errors']}")
        if "data" not in result:
            raise KeyError(f"No data in result, probably rate limit exceeded: {result}")
        return result
    
    def try_fetch_stratz_match(self, client, match_id):
        query = """
            query($id: Long!) {
                match(id: $id) {
                    id
                    parsedDateTime
                }
            }
        """
        match = self.fetch_stratz(client, query, variables={'id': match_id})['data']['match']
        if not match:
            return False
        parsed_timestamp = match.get('parsedDateTime', None)
        if not parsed_timestamp:
            return False
        is_saved = self.fetch_stratz_matches([match_id])
        if is_saved:
            logging.info(f'Successfully fetched data from stratz for ID {match_id}')
            return is_saved
        else:
            logging.error(f'Failed to fetch match details from stratz for ID {match_id}')
            return False

    def fetch_stratz_matches(self, match_ids):
        query = """
            query($id: Long!) {
                match(id: $id) {
                    id
                    tournamentId
                    tournamentRound
                    leagueId
                    radiantTeamId
                    direTeamId
                    seriesId
                    gameVersionId
                    regionId
                    clusterId
                    didRadiantWin
                    startDateTime
                    endDateTime
                    durationSeconds
                    firstBloodTime
                    towerStatusRadiant
                    towerStatusDire
                    barracksStatusRadiant
                    barracksStatusDire
                    rank
                    actualRank
                    averageRank
                    averageImp
                    bracket
                    analysisOutcome
                    topLaneOutcome
                    midLaneOutcome
                    bottomLaneOutcome
                    predictedOutcomeWeight
                    pickBans {
                        isPick
                        heroId
                        order
                        isRadiant
                    }
                    chatEvents {
                        time
                        type
                        fromHeroId
                        toHeroId
                        value
                        pausedTick
                        isRadiant
                    }
                    predictedWinRates
                    winRates
                    radiantNetworthLeads
                    radiantExperienceLeads
                    radiantKills
                    direKills
                    towerDeaths {
                        time
                        npcId
                        isRadiant
                        attacker
                    }
                    towerStatus {
                        towers {
                            npcId
                            hp
                        }
                    outposts {
                        npcId
                        isControlledByRadiant
                        isRadiantSide
                    }
                }
                players {
                heroId
                steamAccountId
                partyId
                steamAccount {
                    name
                    realName
                    profileUri
                    timeCreated
                    isAnonymous
                    proSteamAccount {
                        teamId
                        name
                    }
                }
                kills
                deaths
                assists
                isRadiant
                isVictory
                variant
                imp
                lane
                position
                networth
                goldPerMinute
                goldSpent
                towerDamage
                heroDamage
                intentionalFeeding
                stats {
                    impPerMinute
                    goldPerMinute
                    networthPerMinute
                    experiencePerMinute
                    towerDamagePerMinute
                    campStack
                    locationReport {
                    positionX
                    positionY
                    }
                    deathEvents {
                    time
                    attacker
                    isDieBack
                    positionX
                    positionY
                    }
                    farmDistributionReport {
                    creepLocation {
                        id
                        gold
                    }
                    neutralLocation {
                        id
                        gold
                    }
                    ancientLocation {
                        id
                        gold
                    }
                    buildings {
                        id
                        gold
                    }
                    bountyGold {
                        id
                        gold
                    }
                    other {
                        id
                        gold
                    }
                    buyBackGold
                    }
                    matchPlayerBuffEvent {
                    time
                    abilityId
                    itemId
                    stackCount
                    }
                    inventoryReport {
                    item0 {
                        itemId
                    }
                    item1 {
                        itemId
                    }
                    item2 {
                        itemId
                    }
                    item3 {
                        itemId
                    }
                    item4 {
                        itemId
                    }
                    item5 {
                        itemId
                    }
                    neutral0 {
                        itemId
                    }
                    }
                    itemPurchases {
                    time
                    itemId
                    }
                    courierKills {
                    time
                    }
                    runes {
                    time
                    rune
                    action
                    positionX
                    positionY
                    }
                    wards {
                    time
                    type
                    positionX
                    positionY
                    }
                    wardDestruction {
                    time
                    gold
                    isWard
                    }
                }
                }
            }
            }
        """
        table_map = {
            'details': 'match_details', 'pickBans': 'match_pick_bans', 'chatEvents': 'match_chat_events',
            'predictedWinRates': 'match_predicted_win_rates', 'winRates': 'match_win_rates', 
            'leads': 'match_leads', 'kills': 'match_kills', 'towerDeaths': 'match_tower_deaths', 'towerStatus': 'match_tower_updates', 
            'snapshots': 'match_snapshots', 'outposts': 'match_outpost_updates', 'players': 'match_players', 
            'impPerMinute': 'match_imp_per_minute', 'performanceMetrics': 'match_performance_metrics', 
            'locationReport': 'match_position', 'deathEvents': 'match_death_events', 'farmDistributionReport': 'match_farm', 
            'itemPurchases': 'match_purchases', 'courierKills': 'match_courier_kills', 'runes': 'match_runes',
            'wards': 'match_wards', 'wardDestruction': 'match_ward_destructions'
        }

        storage = {key: [] for key in table_map.keys()}
        with httpx.Client(headers=self.stratz_headers) as client:
            for iteration, match_id in enumerate(match_ids):
                if iteration % 100 == 0: 
                    self._flush_storage(storage, table_map)
                    storage = {key: [] for key in table_map.keys()}
                logging.info(f"Processing {match_id} ({iteration+1}/{len(match_ids)})")
                try:
                    variables = {'id': match_id}
                    match_json = self.fetch_stratz(client, query, variables=variables)['data']['match']
                    if not match_json:
                        logging.warning(f"There was no match data for match {match_id} ({iteration+1}/{len(match_ids)})")
                        continue

                    mid = match_json['id']
                    match_details = {}
                    for key, value in match_json.items():
                        if type(value) != list and value is not None:
                            match_details[key] = value
                    storage['details'].append(match_details)

                    pb = match_json.get('pickBans', [])
                    if pb:
                        for entry in pb: 
                            entry['match_id'] = mid
                        storage['pickBans'].extend(pb)
                    else:
                        pass
                    ce = match_json.get('chatEvents', [])
                    if ce:
                        for entry in ce:
                            entry['match_id'] = mid
                        storage['chatEvents'].extend(ce)
                    else:
                        pass
                    try:
                        storage['winRates'].extend([
                            {
                                'match_id': mid, 
                                'minute': minute, 
                                'win_rates': rate
                            }
                            for minute, rate in enumerate(match_json['winRates'])
                        ])
                    except:
                        pass
                    try:
                        storage['predictedWinRates'].extend([
                            {
                                'match_id': mid, 
                                'minute': minute, 
                                'predicted_win_rate': rate
                            }
                            for minute, rate in enumerate(match_json['predictedWinRates'])
                        ])
                    except:
                        pass
                    try:
                        storage['leads'].extend([
                            {
                                'match_id': mid,
                                'minute': minute,
                                'radiantNetworthLeads': rnwl,
                                'radiantExperienceLeads': rel,
                            }
                            for minute, (rnwl, rel) in enumerate(zip(match_json['radiantNetworthLeads'], match_json['radiantExperienceLeads']))
                        ])
                    except:
                        pass
                    try:
                        storage['kills'].extend([
                            {
                                'match_id': mid,
                                'minute': minute,
                                'radiantKills': rk,
                                'direKills': dk
                            }
                            for minute, (rk, dk) in enumerate(zip(match_json['radiantKills'], match_json['direKills']))
                        ])
                    except:
                        pass
                    td = match_json.get('towerDeaths', [])
                    if td:
                        for entry in td:
                            entry['match_id'] = mid
                        storage['towerDeaths'].extend(td)
                    else:
                        pass

                    snapshots = []
                    tower_updates = []
                    outpost_updates = []
                    tower_status = match_json.get('towerStatus', [])
                    if tower_status:
                        for index, buildings in enumerate(match_json['towerStatus']):
                            snapshot_id = str(match_json['id']) + f'_{index}'
                            snapshots.append(
                            {
                                'snapshot_id': snapshot_id,
                                'match_id': match_json['id'],
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
                    for idx, player in enumerate(match_json['players']):
                        try:
                            hero_id = player['heroId']
                            player_row = {'match_id': mid}
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
                                    'match_id': mid,
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
                                    'match_id': mid,
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
                                                'match_id': mid,
                                                'hero_id': hero_id,
                                                'source_type': source_type, 
                                                'id': v['id'],
                                                'gold': v['gold']
                                            }
                                            for v in items
                                    ])
                                else:
                                    storage['farmDistributionReport'].append({
                                        'match_id': mid,
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
                                    'match_id': mid,
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
                                    entry['match_id'] = mid
                                    entry['hero_id'] = hero_id
                                storage[hero_stat].extend(hs)

                except Exception as e:
                    logging.exception(f"Error on match {match_id}: {e}")
                    continue
                logging.info(f"Iteration {iteration} with match {match_id} processed successfully")
            self._flush_storage(storage, table_map)
            return True

    def _flush_storage(self, storage, table_map):
        for key, data_list in storage.items():
            if not data_list: 
                continue               
            df = pd.DataFrame(data_list)
            renames = {
                'leads': {'radiantNetworthLeads': 'radiant_networth_leads', 'radiantExperienceLeads': 'radiant_experience_leads'},
                'kills': {'radiantKills': 'radiant_kills', 'direKills': 'dire_kills'},
                'towerStatus': {'npcId': 'npc_id'},
                'outposts': {
                    'npcId': 'npc_id',
                    'isControlledByRadiant': 'is_radiant_controlled', 
                    'isRadiantSide': 'is_radiant_side'
                },
                'deathEvents': {'positionX': 'position_x', 'positionY': 'position_y'},
            }
            
            if key in renames:
                df = df.rename(columns=renames[key])
            table_name = table_map[key]
            if table_name == 'match_farm':
                self.insert_df_into_table(df, table_name, conflict_cols=['farm_id'])
            else:
                self.insert_df_into_table(df, table_name, conflict_cols=['id'])
            self.query_execute('REFRESH MATERIALIZED VIEW hero_pick_ban_stats;')
            self.query_execute('REFRESH MATERIALIZED VIEW hero_winrate_stats')
            logging.info(f"Bulk inserted {len(df)} rows into {table_name}")
    
    def fetch_opendota(self, client: httpx.Client, endpoint):
        response = client.get(f'{self.opendota_url}/{endpoint}') 
        try:
            response.raise_for_status()
            result = response.json()
            return result
        except:
            logging.error(f"Failed GET request at {self.opendota_url}/{endpoint}")
            return []
        
    def request_parse_opendota(self, client: httpx.Client, match_id):
        """Request parsing match_details from opendota. Returns job id"""
        try:
            response = client.post(f'{self.opendota_url}/request/{match_id}').json()
            return response['job']['jobId']
        except Exception as e:
            logging.error(f'Failed to request match parsing at opendota: {e}')

    def is_match_parsed_opendota(self, client: httpx.Client, job_id):
        response = client.get(f'{self.opendota_url}/request/{job_id}')
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
    
    def fetch_match_opendota(self, client: httpx.Client, match_id):
        #TODO: refactor and optimize
        try:
            response = client.get(f'{self.opendota_url}/matches/{match_id}')
            response.raise_for_status()
            result = response.json()
            rune_map = {
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
            mid = result['match_id']
            table_names = [
                'match_details', 'match_death_events', 'match_pick_bans', 'match_tower_deaths', 
                'match_players', 'match_purchases', 'match_runes', 'match_wards'
            ]
            storage = {table: [] for table in table_names}
            picks_bans = result.get('picks_bans', [])
            for mpb in picks_bans:
                storage['match_pick_bans'].append(
                    {
                        'match_id': mid,
                        'isPick': mpb['is_pick'],
                        'heroId': mpb['hero_id'],
                        'order': mpb['order'],
                        'isRadiant': mpb['team'] == 0
                    }
                )
            storage['match_details'] = {
                'id': mid, 'tournamentId': result.get('tournament_id'), 'tournamentRound': result.get('tournament_round'),
                'leagueId': result['leagueid'], 'radiantTeamId': result.get('radiant_team_id'), 'direTeamId': result.get('dire_team_id'),
                'seriesId': result['series_id'], 'clusterId': result['cluster'], 'didRadiantWin': result['radiant_win'],
                'startDateTime': result['start_time'], 'endDateTime': result['start_time'] + result['duration'], 'durationSeconds': result['duration'],
                'firstBloodTime': result['first_blood_time'], 'towerStatusRadiant': result['tower_status_radiant'], 'towerStatusDire': result['tower_status_dire'],
                'barracksStatusRadiant': result['barracks_status_radiant'], 'barracksStatusDire': result['barracks_status_dire'], 'rank': result.get('rank_tier'),
                'actualRank': result.get('rank_tier_actual'), 'averageRank': result.get('average_rank'), 'averageImp': result.get('average_imp'),
                'radiant_score': result['radiant_score'], 'dire_score': result['dire_score']
            }
            for obj in result['objectives']:
                if obj['type'] == 'building_kill':
                    try:
                        attacker = self.heroes[self.heroes['name'] == obj['unit']].get('id').iloc[0]
                    except:
                        attacker = 'non-hero'
                    storage['match_tower_deaths'].append(
                        {
                            'match_id': mid,
                            'time': obj['time'],
                            'npcId': self.npcs[self.npcs['name'] == obj['key']].get('id').iloc[0],
                            'isRadiant': 'goodguys' in obj['key'],
                            'attacker': attacker
                        }
                    )
            for p in result['players']:
                hero_id = p['hero_id']
                for kill in p['kills_log']:
                    try: 
                        killed_id = int(self.heroes[self.heroes['name'] == kill['key']].get('id').iloc[0])
                    except:
                        killed_id = -1
                    storage['match_death_events'].append(
                        {
                            'match_id': mid,
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
                        'match_id': mid,
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
                for pur in p['purchase_log']:
                    storage['match_purchases'].append(
                        {
                            'match_id': mid,
                            'hero_id': hero_id,
                            'time': pur['time'],
                            'itemId': self.items[self.items['shortName'] == pur['key']].get('id').iloc[0]
                        }
                    )
                for rune in p['runes_log']:
                    storage['match_runes'].append(
                        {
                            'match_id': mid,
                            'hero_id': p['hero_id'],
                            'time': rune['time'],
                            'rune': rune_map[rune['key']]
                        }
                    )
                for ward in p['obs_log']:
                    storage['match_wards'].append(
                        {
                            'match_id': mid,
                            'hero_id': p['hero_id'],
                            'time': ward['time'],
                            'type': 0,
                            'positionX': ward['x'],
                            'positionY': ward['y']
                        }
                    )
                for ward in p['sen_log']:
                    storage['match_wards'].append(
                        {
                            'match_id': mid,
                            'hero_id': p['hero_id'],
                            'time': ward['time'],
                            'type': 1,
                            'positionX': ward['x'],
                            'positionY': ward['y']
                        }
                    )  
            for table, data in storage.items():
                if table == 'match_details':
                    self.insert_df_into_table(pd.DataFrame(data, index=[0]), table_name=table)
                else:
                    self.insert_df_into_table(pd.DataFrame(data), table_name=table)
            logging.info(f"Successfully fetched and stored data for match ID {match_id}")

        except Exception as e:
            logging.error(f'Failed to parse match at opendota: {e}')
            raise

    def get_pg_type(self, pandas_type):
        if pd.api.types.is_integer_dtype(pandas_type):
            return "BIGINT" 
        elif pd.api.types.is_float_dtype(pandas_type):
            return "DOUBLE PRECISION"
        elif pd.api.types.is_bool_dtype(pandas_type):
            return "BOOLEAN"
        elif pd.api.types.is_datetime64_any_dtype(pandas_type):
            return "TIMESTAMP"
        else:
            return "TEXT"