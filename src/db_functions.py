import pandas as pd 
import psycopg
from psycopg.types.json import Jsonb
from psycopg import sql
import httpx
import time

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
    
def query_select(conn_str, query, identifiers=None, params=None):
    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            if identifiers:
                final_query = sql.SQL(query).format(*[sql.Identifier(name) for name in identifiers])
            else:
                final_query = sql.SQL(query)
            cur.execute(final_query, params)
            if cur.description:
                return cur.fetchall()
            else:
                return None
    
def query_select_to_df(conn_str, query, table_name=None, columns=None, identifiers=None, params=None):
    with psycopg.connect(conn_str) as conn:
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
        
def query_execute(conn_str, query, identifiers=None, params=None):
    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            if identifiers:
                final_query = sql.SQL(query).format(*[sql.Identifier(name) for name in identifiers])
            else:
                final_query = sql.SQL(query)
            cur.execute(final_query, params)
            conn.commit()
            return None
    
def create_table_from_df(df, table_name, conn_str, convert_dtypes=True, add_serial_id=False, jsonb_cols=[]):
    # 1. Generate column definitions
    if convert_dtypes:
        schema_df = df.convert_dtypes()
    else:
        schema_df = df
    try:
        with psycopg.connect(conn_str) as conn:
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

def insert_df_into_table(df, table_name, conn_str, jsonb_cols=[]):
    df = df.convert_dtypes()
    clean_df = df.astype(object).where(pd.notnull(df), None)
    for col in jsonb_cols:
        if col in clean_df.columns:
            clean_df[col] = clean_df[col].apply(lambda x: Jsonb(x) if x is not None else None)
    try:
        with psycopg.connect(conn_str) as conn:
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

def query_stratz(query: str, headers, api_url, variables={}):
    with httpx.Client(headers=headers) as client:
        response = client.post(
            url=api_url,
            json={'query': query, 'variables': variables}
        )
        result = response.json()
        if "errors" in result:
            raise Exception(f"GraphQL Error: {result['errors']}")
        return result
    
def query_match(conn_str, headers, api_url, match_ids):
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
    ## Preparing column lists for parsing matches to sql
    cols_to_include = [
        'id',
        'tournamentId',
        'tournamentRound',
        'leagueId',
        'radiantTeamId',
        'direTeamId',
        'seriesId',
        'gameVersionId',
        'regionId',
        'clusterId',
        'didRadiantWin',
        'startDateTime',
        'endDateTime',
        'durationSeconds',
        'firstBloodTime',
        'towerStatusRadiant',
        'towerStatusDire',
        'barracksStatusRadiant',
        'barracksStatusDire',
        'rank',
        'actualRank',
        'averageRank',
        'averageImp',
        'bracket',
        'analysisOutcome',
        'topLaneOutcome',
        'midLaneOutcome',
        'bottomLaneOutcome',
        'predictedOutcomeWeight'
    ]
    performance_metrics_columns = [
        'match_id',
        'hero_id',
        'minute',
        'gold_per_minute',
        'networth_per_minute',
        'experience_per_minute',
        'tower_damage_per_minute',
        'camp_stack'
    ]
    for match_id in match_ids:
        start_time = time.time()
        variables = {'id': match_id}
        result = query_stratz(query, headers=headers, api_url=api_url, variables=variables)
        result_json = result['data']['match']
        #TODO: find first blood team by looking for chat event type 5
        #TODO: both hero IDs present: tip
        #TODO: find out what is roshan kills etc. from an actual replay
        filtered_match_details = {k: result_json[k] for k in cols_to_include}
        df_match_details = pd.DataFrame([filtered_match_details])
        df_pickbans = pd.DataFrame(result_json['pickBans'])
        df_pickbans.insert(0, 'match_id', result_json['id'])
        try:
            df_chatevents = pd.json_normalize(result_json['chatEvents'])
        except:
            result = query_stratz(query, headers=headers, api_url=api_url, variables=variables)
            result_json = result['data']['match']
            try:
                df_chatevents = pd.json_normalize(result_json['chatEvents'])
            except:
                continue
        df_chatevents.insert(0, 'match_id', result_json['id'])
        try:
            df_predicted_win_rates = pd.DataFrame({
                'match_id': result_json['id'],
                'predicted_win_rate': result_json['predictedWinRates']
            })
        except:
            result = query_stratz(query, headers=headers, api_url=api_url, variables=variables)
            result_json = result['data']['match']
            try:
                df_predicted_win_rates = pd.DataFrame({
                'match_id': result_json['id'],
                'predicted_win_rate': result_json['predictedWinRates']
                })
            except:
                continue
        df_win_rates = pd.DataFrame({
            'match_id': result_json['id'],
            'win_rates': result_json['winRates'], 
        })
        df_kills = pd.DataFrame({
            'match_id': result_json['id'],
            'radiant_kills': result_json['radiantKills'],
            'dire_kills': result_json['direKills']
        })
        df_leads = pd.DataFrame({
            'match_id': result_json['id'],
            'radiant_networth_leads': result_json['radiantNetworthLeads'],
            'radiant_experience_leads': result_json['radiantExperienceLeads']
        })
        df_tower_deaths = pd.json_normalize(result_json['towerDeaths'])
        df_tower_deaths.insert(0, 'match_id', result_json['id'])
        snapshots = []
        tower_updates = []
        outpost_updates = []
        for i, snapshot in enumerate(result_json['towerStatus']):
            snapshot_id = f"{result_json['id']}_{i}"
            snapshots.append({
                'snapshot_id': snapshot_id,
                'match_id': result_json['id'],
                'order_index': i 
            })
            for t in snapshot['towers']:
                tower_updates.append({
                    'snapshot_id': snapshot_id,
                    'npc_id': t['npcId'],
                    'hp': t['hp']
                })
                
            for o in snapshot['outposts']:
                outpost_updates.append({
                    'snapshot_id': snapshot_id,
                    'npc_id': o['npcId'],
                    'is_radiant_controlled': o['isControlledByRadiant'],
                    'is_radiant_side': o['isRadiantSide']
                })
        df_snapshots = pd.DataFrame(snapshots)
        df_tower_updates = pd.DataFrame(tower_updates)
        df_outpost_updates = pd.DataFrame(outpost_updates)
        df_players = pd.json_normalize(result_json['players'])
        df_players.insert(0, 'match_id', result_json['id'])
        og_cols = []
        stat_cols = []
        for colname in df_players.columns:
            if colname.startswith('steamAccount.'):
                og_cols.append(colname)
                continue
            if colname.startswith('stats.'):
                stat_cols.append(colname)
        new_cols = [str.replace(colname[13:], '.', '_') for colname in og_cols]
        col_mapper = {og_col: new_col for og_col, new_col in zip(og_cols, new_cols)}
        df_players = df_players.rename(col_mapper, axis=1)
        df_players = df_players.drop(stat_cols, axis=1)
        df_performance_metrics = pd.DataFrame(columns=performance_metrics_columns)
        df_death_events = pd.DataFrame(columns=['match_id', 'hero_id', 'time', 'attacker', 'isDieBack'])
        df_farm = pd.DataFrame(columns=['match_id', 'hero_id', 'source_type', 'id',	'gold'])
        df_courier_kills = pd.DataFrame(columns=['match_id', 'hero_id', 'time'])
        df_runes = pd.DataFrame(columns=['match_id', 'hero_id', 'time', 'rune', 'action', 'positionX', 'positionY'])
        df_wards = pd.DataFrame(columns=[
            'match_id',
            'hero_id',
            'time',
            'type',
            'positionX',
            'positionY'
        ])
        df_ward_destructions = pd.DataFrame(columns=[
            'match_id',
            'hero_id',
            'time',
            'gold',
            'isWard'
        ])
        df_inventory_reports = pd.DataFrame(columns=[
            'match_id',
            'hero_id',
            'minute',
            'item0_id',
            'item1_id',
            'item2_id',
            'item3_id',
            'item4_id',
            'item5_id',
            'neutral0_id',
        ])
        df_purchases = pd.DataFrame(columns=['match_id', 'hero_id', 'time', 'itemId'])
        df_buffs = pd.DataFrame(columns=[
            'match_id',
            'hero_id',
            'time',
            'abilityId',
            'itemId',
            'stackCount'
        ])
        df_imp_per_minute = pd.DataFrame(columns=['match_id', 'hero_id', 'imp_per_minute'])
        for idx, player in enumerate(result_json['players']):
            stats = player['stats'] 

            df_ir = pd.json_normalize(stats['inventoryReport'])
            existing_item_cols = [c for c in df_ir.columns if '.itemId' in c]
            df_ir = df_ir[existing_item_cols].copy()
            df_ir = df_ir.rename(columns=lambda x: x.replace('.itemId', '_id'))
            df_ir.insert(0, 'hero_id', player['heroId'])
            df_ir.insert(0, 'match_id', result_json['id'])
            df_inventory_reports = pd.concat([df_inventory_reports, df_ir])
            df_ipm = pd.DataFrame({
                'match_id': result_json['id'],
                'hero_id': player['heroId'],
                'imp_per_minute': stats['impPerMinute']
            }) 
            df_imp_per_minute = pd.concat([df_imp_per_minute, df_ipm])
            df_pm = pd.DataFrame({
                'match_id': result_json['id'],
                'hero_id': player['heroId'],
                'minute': range(len(stats['networthPerMinute'])),
                'gold_per_minute': pd.Series(stats['goldPerMinute']),
                'networth_per_minute': pd.Series(stats['networthPerMinute']),
                'experience_per_minute': pd.Series(stats['experiencePerMinute']),
                'tower_damage_per_minute': pd.Series(stats['towerDamagePerMinute']),
                'camp_stack': pd.Series(stats['campStack'])
            })
            df_performance_metrics = pd.concat([df_performance_metrics, df_pm])
            df_matchid_heroid = pd.DataFrame({
                'match_id': result_json['id'],
                'hero_id': player['heroId']
            }, index=range(len(stats['deathEvents'])))
            df_de = pd.DataFrame(stats['deathEvents'])
            df_death_events = pd.concat([df_death_events, pd.concat([df_matchid_heroid, df_de], axis=1)])
            rows = []
            for category, content in stats['farmDistributionReport'].items():
                if isinstance(content, list):
                    for entry in content:
                        # Copy entry so we don't modify the original JSON
                        row = entry.copy()
                        row['source_type'] = category
                        rows.append(row)
                elif isinstance(content, dict):
                    row = content.copy()
                    row['source_type'] = category
                    rows.append(row)
            df_f = pd.DataFrame(rows)
            df_f.insert(0, 'hero_id', player['heroId'])
            df_f.insert(0, 'match_id', result_json['id'])
            df_farm = pd.concat([df_farm, df_f])
            buff_rows = []
            for buff in stats['matchPlayerBuffEvent']:
                buff_rows.append({
                    'time': buff['time'],
                    'item_id': buff['itemId'],
                    'ability_id': buff['abilityId']
                })
            df_b = pd.DataFrame(buff_rows)
            df_b.insert(0, 'hero_id', player['heroId'])
            df_b.insert(0, 'match_id', result_json['id'])
            df_buffs = pd.concat([df_buffs, df_b])

            df_p = pd.DataFrame(stats['itemPurchases'])
            df_p.insert(0, 'hero_id', player['heroId'])
            df_p.insert(0, 'match_id', result_json['id'])
            df_purchases = pd.concat([df_purchases, df_p])
            df_c = pd.DataFrame(stats['courierKills'])
            df_c.insert(0, 'hero_id', player['heroId'])
            df_c.insert(0, 'match_id', result_json['id'])
            df_courier_kills = pd.concat([df_courier_kills, df_c])
            df_r = pd.DataFrame(stats['runes'])
            df_r.insert(0, 'hero_id', player['heroId'])
            df_r.insert(0, 'match_id', result_json['id'])
            df_runes = pd.concat([df_runes, df_r])
            df_w = pd.DataFrame(stats['wards'])
            df_w.insert(0, 'hero_id', player['heroId'])
            df_w.insert(0, 'match_id', result_json['id'])
            df_wards = pd.concat([df_wards, df_w])
            df_wd = pd.DataFrame(stats['wardDestruction'])
            df_wd.insert(0, 'hero_id', player['heroId'])
            df_wd.insert(0, 'match_id', result_json['id'])
            df_ward_destructions = pd.concat([df_ward_destructions, df_wd])
        df_death_events = df_death_events.reset_index().drop(['index'], axis=1)
        first_layer_dfs = [
            df_match_details,
            df_pickbans,
            df_chatevents,
            df_predicted_win_rates,
            df_win_rates,
            df_kills,
            df_leads,
            df_tower_deaths,
            df_snapshots,
            df_tower_updates,
            df_outpost_updates,
            df_players
        ]
        second_layer_dfs = [
            df_performance_metrics, 
            df_death_events,
            df_inventory_reports,
            df_imp_per_minute,
            df_farm,
            df_buffs,
            df_purchases,
            df_courier_kills,
            df_runes,
            df_wards,
            df_ward_destructions
        ]
        if match_id == match_ids[0]:
            ## If it's the first result, create the tables
            create_table_from_df(df_match_details, 'match_details', conn_str=conn_str)
            create_table_from_df(df_pickbans, 'match_pick_bans', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_chatevents, 'match_chat_events', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_predicted_win_rates, 'match_predicted_win_rates', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_win_rates, 'match_win_rates', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_kills, 'match_kills', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_leads, 'match_leads', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_tower_deaths, 'match_tower_deaths', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_snapshots, 'match_snapshots', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_tower_updates, 'match_tower_updates', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_outpost_updates, 'match_outpost_updates', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_players, 'match_players', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_performance_metrics, 'match_performance_metrics', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_death_events, 'match_death_events', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_inventory_reports, 'match_inventory_reports', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_imp_per_minute, 'match_imp_per_minute', conn_str=conn_str, add_serial_id=True)
            df_farm.insert(0, 'farm_id', range(len(df_farm)))
            create_table_from_df(df_farm, 'match_farm', conn_str=conn_str)
            df_farm.drop('farm_id', axis=1, inplace=True)
            create_table_from_df(df_buffs, 'match_buffs', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_purchases, 'match_purchases', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_courier_kills, 'match_courier_kills', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_runes, 'match_runes', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_wards, 'match_wards', conn_str=conn_str, add_serial_id=True)
            create_table_from_df(df_ward_destructions, 'match_ward_destructions', conn_str=conn_str, add_serial_id=True)
        insert_df_into_table(df_match_details, 'match_details', conn_str=conn_str)

        insert_df_into_table(df_pickbans, 'match_pick_bans', conn_str=conn_str)

        insert_df_into_table(df_chatevents, 'match_chat_events', conn_str=conn_str)

        insert_df_into_table(df_predicted_win_rates, 'match_predicted_win_rates', conn_str=conn_str)

        insert_df_into_table(df_win_rates, 'match_win_rates', conn_str=conn_str)

        insert_df_into_table(df_kills, 'match_kills', conn_str=conn_str)

        insert_df_into_table(df_leads, 'match_leads', conn_str=conn_str)

        insert_df_into_table(df_tower_deaths, 'match_tower_deaths', conn_str=conn_str)

        insert_df_into_table(df_snapshots, 'match_snapshots', conn_str=conn_str)

        insert_df_into_table(df_tower_updates, 'match_tower_updates', conn_str=conn_str)

        insert_df_into_table(df_outpost_updates, 'match_outpost_updates', conn_str=conn_str)

        insert_df_into_table(df_players, 'match_players', conn_str=conn_str)

        insert_df_into_table(df_performance_metrics, 'match_performance_metrics', conn_str=conn_str)

        insert_df_into_table(df_death_events, 'match_death_events', conn_str=conn_str)

        insert_df_into_table(df_inventory_reports, 'match_inventory_reports', conn_str=conn_str)

        insert_df_into_table(df_imp_per_minute, 'match_imp_per_minute', conn_str=conn_str)

        insert_df_into_table(df_farm, 'match_farm', conn_str=conn_str)

        insert_df_into_table(df_buffs, 'match_buffs', conn_str=conn_str)

        insert_df_into_table(df_purchases, 'match_purchases', conn_str=conn_str)

        insert_df_into_table(df_courier_kills, 'match_courier_kills', conn_str=conn_str)

        insert_df_into_table(df_runes, 'match_runes', conn_str=conn_str)

        insert_df_into_table(df_wards, 'match_wards', conn_str=conn_str)

        insert_df_into_table(df_ward_destructions, 'match_ward_destructions', conn_str=conn_str)
        elapsed = time.time() - start_time
        if elapsed < 2.0:
            time.sleep(2.0-elapsed)