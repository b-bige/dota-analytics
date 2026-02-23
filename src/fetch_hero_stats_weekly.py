import httpx
import pandas as pd
import numpy as np
import psycopg
from datetime import datetime, timedelta, timezone
import time

import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

import db_functions as dbf
from ratelimit import limits, sleep_and_retry

import logging
import basic_logger
basic_logger.setup_logger()

def main():
    try:
        logging.info("Starting weekly hero_stats data fetching...")
        db = dbf.DotaDB()
        query = 'SELECT id FROM patches ORDER BY id DESC LIMIT 1'
        patch_id = db.query_select(query)[0][0]
        query = '''
            query($gameVersionId: Short) {
                constants {
                    heroes(gameVersionId: $gameVersionId) { 
                        id
                    }
                }
            }
        ''' 
        try:
            results = db.query_stratz(query, variables={'gameVersionId': patch_id})
        except Exception as e:
            logging.error(f"Game versions could not be retrieved from API: {e}")
        hero_ids = [res['id'] for res in results['data']['constants']['heroes']]
        week = get_latest_week_timestamp()
        fetch_insert_hero_stats(db, hero_ids, week)
        fetch_insert_matchup_start(db, hero_ids, week)
        fetch_insert_itp_talent_ability_minmax(db, hero_ids, week)
        fetch_insert_lane_outcome(db, hero_ids, week)
        logging.info(f"Successfully inserted all data.")
    except Exception as e:
        logging.error(f"Weekly hero_stats fetching failed: {str(e)}", exc_info=True)

def get_latest_week_timestamp(): #This gets the latest sunday midnight in UTC that Stratz understands
    now = datetime.now(timezone.utc)
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    days_to_subtract = (now.weekday() + 1) % 7
    sunday_midnight = today_midnight - timedelta(days=days_to_subtract)

    return int(sunday_midnight.timestamp())

def fetch_insert_hero_stats(db: dbf.DotaDB, hero_ids, week):
    logging.info(f"Fetching hero stats for {len(hero_ids)} heroes for week {week}")
    query = '''
        query($heroIds: [Short]!, $week: Long, $bracketBasicIds: [RankBracketBasicEnum]) {
            heroStats {
                stats(heroIds: $heroIds, week: $week, bracketBasicIds: $bracketBasicIds) {
                heroId
                week
                time
                position
                bracketBasicIds
                matchCount
                winCount
                networth
                goldPerMinute
                towerDamage
                disableDuration
                disableCount
                stunDuration
                stunCount
                healingSelf
                healingAllies
                heroDamage
                physicalDamage
                magicalDamage
                physicalDamageReceived
                magicalDamageReceived
                supportGold
                campsStacked
                }
            }
        }
    '''
    variables = {'heroIds': hero_ids, 'week': week, 'bracketBasicIds': 'DIVINE_IMMORTAL'}
    try:
        hero_stats = db.query_stratz(query, variables)['data']['heroStats']['stats']
    except Exception as e:
        logging.error(f"Hero stats could not be retrieved from API: {e}")
    df = pd.DataFrame(hero_stats)
    db.insert_df_into_table(df, 'hero_stats')
    logging.info("Successfully inserted hero statistics data")

def fetch_insert_matchup_start(db: dbf.DotaDB, hero_ids, week):
    logging.info(f"Fetching matchup stats for {len(hero_ids)} heroes for week {week}")
    query = '''
        query($heroIds: [Short]!, $week: Long, $bracketBasicIds: [RankBracketBasicEnum]) {
            heroStats {
                matchUp(heroIds: $heroIds, week: $week, bracketBasicIds: $bracketBasicIds) {
                heroId
                matchCountWith
                matchCountVs
                with {
                    heroId1
                    heroId2
                    week
                    synergy
                    winCount
                    matchCount
                    winsAverage
                    goldEarned
                    xp
                    heroDamage
                    towerDamage
                    firstBloodTime
                    synergy
                    winRateHeroId1
                    winRateHeroId2
                }
                vs {
                    heroId1
                    heroId2
                    week
                    synergy
                    winCount
                    matchCount
                    winsAverage
                    goldEarned
                    xp
                    heroDamage
                    towerDamage
                    firstBloodTime
                    synergy
                    winRateHeroId1
                    winRateHeroId2
                }
            }
        }
    }
    '''
    variables = {'heroIds': hero_ids, 'week': week, 'bracketBasicIds': 'DIVINE_IMMORTAL'}
    try:
        matchups = db.query_stratz(query, variables)['data']['heroStats']['matchUp']
    except Exception as e:
        logging.error(f'Matchups could not be retrieved from API: {e}')
    all_matchups = []
    all_with = []
    all_vs = []
    for hero_data in matchups: 
        matchup = {
            'heroId': hero_data['heroId'],
            'week': week,
            'matchCountWith': hero_data['matchCountWith'],
            'matchCountVs': hero_data['matchCountVs']
        }
        all_matchups.append(matchup)
        if hero_data.get('with'):
            df_temp_with = pd.json_normalize(hero_data['with'])
            all_with.append(df_temp_with)
        if hero_data.get('vs'):
            df_temp_vs = pd.json_normalize(hero_data['vs'])
            all_vs.append(df_temp_vs)
    df_main_stats = pd.DataFrame(all_matchups)
    df_with_stats = pd.concat(all_with, ignore_index=True) if all_with else pd.DataFrame()
    df_vs_stats = pd.concat(all_vs, ignore_index=True) if all_vs else pd.DataFrame()
    db.insert_df_into_table(df_main_stats, 'matchup_stats')
    db.insert_df_into_table(df_with_stats, 'matchup_with')
    db.insert_df_into_table(df_vs_stats, 'matchup_vs')
    logging.info("Successfully inserted matchup statistics data")

def fetch_insert_itp_talent_ability_minmax(db: dbf.DotaDB, hero_ids, week):
    logging.info(f"Fetching item purchase, talent and ability min-max stats for {len(hero_ids)} heroes for week {week}")
    query = '''
        query($heroId: Short!, $week: Long, $bracketBasicIds: [RankBracketBasicEnum]) {
            heroStats {
                itemFullPurchase(heroId: $heroId, week: $week, bracketBasicIds: $bracketBasicIds) {
                heroId
                week
                itemId
                instance
                time
                matchCount
                winCount
                winsAverage
                }
                itemStartingPurchase(heroId: $heroId, week: $week) {
                heroId
                week
                itemId
                instance
                wasGiven
                matchCount
                winCount
                winsAverage
                } 
                talent(heroId: $heroId, week: $week, bracketBasicIds: $bracketBasicIds) {
                heroId
                week
                abilityId
                matchCount
                winCount
                time
                winsAverage
                timeAverage
                }
                abilityMinLevel(heroId: $heroId, week: $week, bracketBasicIds: $bracketBasicIds) {
                heroId
                week
                abilityId
                level
                matchCount
                winCount
                }
                abilityMaxLevel(heroId: $heroId, week: $week, bracketBasicIds: $bracketBasicIds) {
                heroId
                week
                abilityId
                level
                matchCount
                winCount
                }
            }
        }
    '''
    stat_keys = [
    'itemFullPurchase', 'itemStartingPurchase', 'talent', 
    'abilityMinLevel', 'abilityMaxLevel'
    ]

    table_mapping = { #Maps API keys to the table names
        'itemFullPurchase': 'hero_item_full_purchase',
        'itemStartingPurchase': 'hero_item_starting_purchase',
        'talent': 'hero_talent',
        'abilityMinLevel': 'hero_ability_min',
        'abilityMaxLevel': 'hero_ability_max'
    }
    data_accumulator = {key: [] for key in stat_keys}
    for hero_id in hero_ids:
        variables = {'heroId': hero_id, 'week': week, 'bracketBasicIds': 'DIVINE_IMMORTAL'}
        try:
            results = db.query_stratz(query, variables)['data']['heroStats']
            for key in stat_keys:
                    if results.get(key):
                        data_accumulator[key].extend(results[key])
        except Exception as e:
            logging.error(f"Failed to fetch hero {hero_id} for week {week}: {e}")
        time.sleep(0.06)
    for key, data_list in data_accumulator.items():
        if not data_list:
            continue
            
        df = pd.DataFrame(data_list)
        table_name = table_mapping[key]
        if 'id' in df.columns:
            df = df.drop(columns=['id'])
            
        db.insert_df_into_table(df, table_name)
    logging.info(f"Successfully inserted item purchase timings, talent and ability min-max statistics data")

def fetch_insert_lane_outcome(db: dbf.DotaDB, hero_ids, week):
    logging.info(f"Fetching lane outcome stats for {len(hero_ids)} heroes for week {week}")
    query = '''
        query($heroId: Short, $week: Long, $bracketBasicIds: [RankBracketBasicEnum], $isWith: Boolean!) {
            heroStats {
                laneOutcome(heroId: $heroId, week: $week, bracketBasicIds: $bracketBasicIds, isWith: $isWith) {
                    heroId1
                    heroId2
                    week
                    position
                    matchCount
                    drawCount
                    winCount
                    lossCount
                    stompWinCount
                    stompLossCount
                    matchWinCount
                    csCount
                }
            }
        }
    '''
    lane_outcome_data = []
    for is_with in [True, False]:
        for hero_id in hero_ids:
            variables = {'heroId': hero_id, 'week': week, 'bracketBasicIds': 'DIVINE_IMMORTAL', 'isWith': is_with}
            try:
                results = db.query_stratz(query, variables)['data']['heroStats']['laneOutcome']
            except Exception as e:
                logging.error(f"Lane outcome could not be retrieved from API: {e}")
            lane_outcome_data.extend(results)
            time.sleep(0.06)
    df_lane_outcome = pd.DataFrame(lane_outcome_data)
    db.insert_df_into_table(df_lane_outcome, 'matchup_lane_outcome')
    logging.info("Successfully inserted lane outcome data")

if __name__ == '__main__':
    main()