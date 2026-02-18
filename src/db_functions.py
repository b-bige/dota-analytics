import pandas as pd 
import psycopg
from psycopg.types.json import Jsonb
from psycopg import sql
import httpx
import time
import os
from dotenv import load_dotenv
import logging

class DotaDB:
    def __init__(self):
        load_dotenv()
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        dbname = os.getenv("DB_NAME")
        
        self.conn_str = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        self.api_key = os.getenv("API_KEY")
        self.api_url = 'https://api.stratz.com/graphql'
        self.headers = {
            'User-Agent': 'STRATZ_API',
            "Authorization": f"Bearer {self.api_key}"
        }

    def query_select(self, query, identifiers=None, params=None):
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                if identifiers:
                    final_query = sql.SQL(query).format(*[sql.Identifier(name) for name in identifiers])
                else:
                    final_query = sql.SQL(query)

                cur.execute(final_query, params)
                return cur.fetchall() if cur.description else None
            
    def query_select_to_df(self, query, table_name=None, columns=None, identifiers=None, params=None):
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
                        colnames = columns
                    else:
                        colname_query = 'SELECT column_name FROM information_schema.columns WHERE table_name = %s'
                        cur.execute(colname_query, params=(table_name, ))
                        colnames = [colname[0] for colname in cur.fetchall()]
                    return pd.DataFrame(data, columns=colnames)
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
                        pg_type = get_pg_type(dtype)
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
            print(f"Error creating table '{table_name}': {e}")
            return
        print(f"Table '{table_name}' created successfully.")

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
                    seq_query = f"SELECT setval(pg_get_serial_sequence('\"{table_name}\"', 'id'), max(id)) FROM \"{table_name}\";"
                    cur.execute(seq_query) #TODO: edit seq_query so it finds the first column with id in lowercase
                conn.commit()
        except Exception as e:
            print(f"Error inserting data into table '{table_name}': {e}")
            return
        print(f"Data inserted into table '{table_name}' successfully.")

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
            
    def query_stratz(self, query: str, variables={}):
        with httpx.Client(headers=self.headers) as client:
            response = client.post(
                url=self.api_url,
                json={'query': query, 'variables': variables}
            )
            result = response.json()
            if "errors" in result:
                raise Exception(f"GraphQL Error: {result['errors']}")
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
                    deathEvents {
                    time
                    attacker
                    isDieBack
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
            'leads': 'match_leads', 'towerDeaths': 'match_tower_deaths', 'towerStatus': 'match_tower_updates', 
            'snapshots': 'match_snapshots', 'outposts': 'match_outposts', 'players': 'match_players', 
            'impPerMinute': 'match_imp_per_minute', 'performanceMetrics': 'match_performance_metrics', 
            'deathEvents': 'match_death_events', 'farmDistributionReport': 'match_farm', 
            'itemPurchases': 'match_purchases', 'courierKills': 'match_courier_kills', 'runes': 'match_runes',
            'wards': 'match_wards', 'wardDestruction': 'match_ward_destructions'
        }

        # 2. Initialize storage for ALL matches
        storage = {key: [] for key in table_map.keys()}

        for iteration, match_id in enumerate(match_ids):
            logging.info(f"Processing {match_id} ({iteration+1}/{len(match_ids)})")
            
            try:
                # Fetch data
                variables = {'id': match_id}
                result = self.query_stratz(query, variables=variables)
                match_json = result['data']['match']
                if not match_json: continue

                mid = match_json['id']
                match_details = {}
                for key, value in match_json.items():
                    if type(value) != list:
                        match_details[key] = value
                storage['details'].append(match_details)

                # PickBans (Extend because it's a list)
                pb = match_json.get('pickBans', [])
                for entry in pb: 
                    entry['match_id'] = mid
                storage['pickbans'].extend(pb)
                
                ce = match_json.get('chatEvents', [])
                for entry in ce:
                    entry['match_id'] = mid
                storage['chatEvents'].extend(ce)

                storage['win_rates'].extend([
                    {
                        'match_id': mid, 
                        'minute': minute, 
                        'win_rate': rate
                    }
                    for minute, rate in enumerate(match_json['winRates'])
                ])
                storage['predicted_win_rates'].extend([
                    {
                        'match_id': mid, 
                        'minute': minute, 
                        'win_rate': rate
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
                    for minute, (rnwl, rel) in enumerate(zip(match_json['radiantNetWorthleads'], match_json['radiantExperienceLeads']))
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
                    entry('match_id') = mid
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

                    towers = buildings['towers']
                    for entry in towers:
                        entry['snapshot_id'] = snapshot_id
                    tower_updates.append(towers)

                    outposts = buildings['outposts']
                    for entry in outposts:
                        entry['snapshot_id'] = snapshot_id
                    outpost_updates.append(outposts)
                storage['snapshots'].extend(snapshots)
                storage['towerStatus'].extend(tower_updates)
                storage['outposts'].extend(outpost_updates)

                # Players & Stats (The big nested loop)
                for player in match_json.get('players', []):
                    hid = player['heroId']
                    
                    # Flatten player basic info
                    p_info = pd.json_normalize(player).to_dict(orient='records')[0]
                    p_info['match_id'] = mid
                    storage['players'].append(p_info)

                    # Performance Metrics (Time series data)
                    stats = player.get('stats', {})
                    if 'networthPerMinute' in stats:
                        for minute, nw in enumerate(stats['networthPerMinute']):
                            storage['performance'].append({
                                'match_id': mid, 'hero_id': hid, 'minute': minute,
                                'networth': nw, 
                                'gpm': stats['goldPerMinute'][minute] if minute < len(stats['goldPerMinute']) else None
                            })

                # --- END PARSING ---

            except Exception as e:
                logging.error(f"Error on match {match_id}: {e}")
                continue

            # Rate limiting: Stratz is strict
            time.sleep(1.0) 

        # 3. Final Bulk Insertion (Outside the loop!)
        for key, data_list in storage.items():
            if not data_list: continue
            
            df = pd.DataFrame(data_list)
            table_name = table_map[key]
            
            # Create table if first run, then COPY
            # Use your COPY-based method here for speed
            self.insert_df_into_table(df, table_name)
            logging.info(f"Bulk inserted {len(df)} rows into {table_name}")

def get_pg_type(pandas_type):
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
    
