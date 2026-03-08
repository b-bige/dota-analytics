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
    def __init__(self, schema: str='public'):
        load_dotenv()
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        dbname = os.getenv("DB_NAME")
        
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

    def query_select(self, query, identifiers=None, params=None):
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                if identifiers:
                    final_query = sql.SQL(query).format(*[sql.Identifier(name) for name in identifiers])
                else:
                    final_query = sql.SQL(query)
                cur.execute(final_query, params)
                return cur.fetchall() if cur.description else None
            
    def query_select_to_df(self, query, columns=None, identifiers=None, params=None):
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
                return None
            
    def create_table_from_df(self, df, table_name, convert_dtypes=True, add_serial_id=False, jsonb_cols=[]):
        # 1. Generate column definitions
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
                        # Wrap column names in quotes to handle spaces or reserved words
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

    def insert_df_into_table(self, df, table_name, jsonb_cols=[]):
        df = df.convert_dtypes()
        clean_df = df.astype(object).where(pd.notnull(df), None)
        for col in jsonb_cols:
            if col in clean_df.columns:
                clean_df[col] = clean_df[col].apply(lambda x: Jsonb(x) if x is not None else None)
        try:
            with psycopg.connect(self.conn_str) as conn:
                with conn.cursor() as cur:
                    col_names_str = ", ".join([f'"{c}"' for c in clean_df.columns])
                    copy_query = f'COPY "{table_name}" ({col_names_str}) FROM STDIN'
                    with cur.copy(copy_query) as copy:
                        for row in clean_df.itertuples(index=False):
                            copy.write_row(row)

                conn.commit()
        except Exception as e:
            logging.error(f"Error inserting data into table '{table_name}': {e}")
            return
        logging.info(f"Inserted {len(clean_df)} rows into table '{table_name}' successfully.")

    def query_execute(self, query, identifiers=None, params=None):
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                if identifiers:
                    final_query = sql.SQL(query).format(*[sql.Identifier(name) for name in identifiers])
                else:
                    final_query = sql.SQL(query)
                cur.execute(final_query, params)
                conn.commit()
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
    def query_stratz(self, client: httpx.Client, query: str, variables:dict={}):
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

    def query_matches(self, match_ids):
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

        # 2. Initialize storage for ALL matches
        storage = {key: [] for key in table_map.keys()}
        with httpx.Client(headers=self.stratz_headers) as client:
            for iteration, match_id in enumerate(match_ids):
                if iteration % 100 == 0: ## After 1000 matches, save and empty memory
                    self._flush_storage(storage, table_map)
                    storage = {key: [] for key in table_map.keys()}
                logging.info(f"Processing {match_id} ({iteration+1}/{len(match_ids)})")
                try:
                    # Fetch data
                    variables = {'id': match_id}
                    match_json = self.query_stratz(client, query, variables=variables)['data']['match']
                    if not match_json:
                        logging.warning(f"There was no match data for match {match_id} ({iteration+1}/{len(match_ids)})")

                    mid = match_json['id']
                    match_details = {}
                    for key, value in match_json.items():
                        if type(value) != list and value is not None:
                            match_details[key] = value
                    storage['details'].append(match_details)

                    # PickBans (Extend because it's a list)
                    pb = match_json.get('pickBans', [])
                    for entry in pb: 
                        entry['match_id'] = mid
                    storage['pickBans'].extend(pb)
                    
                    ce = match_json.get('chatEvents', [])
                    if ce:
                        for entry in ce:
                            entry['match_id'] = mid
                        storage['chatEvents'].extend(ce)
                    else:
                        continue

                    storage['winRates'].extend([
                        {
                            'match_id': mid, 
                            'minute': minute, 
                            'win_rates': rate
                        }
                        for minute, rate in enumerate(match_json['winRates'])
                    ])
                    storage['predictedWinRates'].extend([
                        {
                            'match_id': mid, 
                            'minute': minute, 
                            'predicted_win_rate': rate
                        }
                        for minute, rate in enumerate(match_json['predictedWinRates'])
                    ])
                    storage['leads'].extend([
                        {
                            'match_id': mid,
                            'minute': minute,
                            'radiantNetworthLeads': rnwl,
                            'radiantExperienceLeads': rel,
                        }
                        for minute, (rnwl, rel) in enumerate(zip(match_json['radiantNetworthLeads'], match_json['radiantExperienceLeads']))
                    ])
                    storage['kills'].extend([
                        {
                            'match_id': mid,
                            'minute': minute,
                            'radiantKills': rk,
                            'direKills': dk
                        }
                        for minute, (rk, dk) in enumerate(zip(match_json['radiantKills'], match_json['direKills']))
                    ])

                    td = match_json.get('towerDeaths', [])
                    for entry in td:
                        entry['match_id'] = mid
                    storage['towerDeaths'].extend(td)

                    snapshots = []
                    tower_updates = []
                    outpost_updates = []
                    for index, buildings in enumerate(match_json['towerStatus']):
                        snapshot_id = str(match_json['id']) + f'_{index}'
                        snapshots.append(
                        {
                            'snapshot_id': snapshot_id,
                            'match_id': match_json['id'],
                            'order_index': index
                        })

                        towers = buildings['towers'] ##TODO: also filter this maybe?
                        for entry in towers:
                            entry['snapshot_id'] = snapshot_id
                        tower_updates.extend(towers)

                        outposts = buildings['outposts'] ##TODO: This is often empty, might want to filter?
                        for entry in outposts:
                            entry['snapshot_id'] = snapshot_id
                        outpost_updates.extend(outposts)
                    storage['snapshots'].extend(snapshots)
                    storage['towerStatus'].extend(tower_updates)
                    storage['outposts'].extend(outpost_updates)
                    for idx, player in enumerate(match_json['players']):
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
                        storage['impPerMinute'].extend([
                            {
                                'match_id': mid,
                                'hero_id': hero_id,
                                'minute': minute,
                                'imp_per_minute': imp
                            }
                            for minute, imp in enumerate(stats['impPerMinute']) 
                        ])
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
                        if not stats['farmDistributionReport']:
                            pass
                        else:
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

    def _flush_storage(self, storage, table_map):
        for key, data_list in storage.items():
            if not data_list: 
                continue
                
            df = pd.DataFrame(data_list)
            if key == 'details':
                match_ids = list(df['id'])
                current_ids = [cid[0] for cid in self.query_select('SELECT id FROM match_details')]
                for mid in match_ids.copy():
                    if mid in current_ids:
                        df = df[df['id'] != mid]
            # Mapping of keys to their specific column renames
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
            self.insert_df_into_table(df, table_name)
            logging.info(f"Bulk inserted {len(df)} rows into {table_name}")
    
    def query_opendota(self, client: httpx.Client, endpoint):
        response = client.get(f'{self.opendota_url}/{endpoint}') #TODO: Implement similar client logic to query_matches
        try:
            response.raise_for_status()
            result = response.json()
            return result
        except:
            logging.error(f"Failed GET request at {self.opendota_url}/{endpoint}")
            return []


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
        
    