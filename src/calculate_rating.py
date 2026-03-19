import pandas as pd
import numpy as np
from openskill.models import PlackettLuce

import os, sys, logging

sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/logger'))

from db_functions import DotaDB
from basic_logger import setup_logger

CORE_WEIGHTS = {
    'gold_per_min':  0.40,  # dominant
    'assists':       0.35,  # nearly as strong
    'net_worth':     0.15,  # positive but weaker once gpm/assists included
    'tower_damage':  0.07,  # positive
    'kills':         0.03,  # weak positive
}

SUPPORT_WEIGHTS = {
    'gold_per_min':  0.35,  # still dominant even for supports
    'assists':       0.40,  # strongest support signal
    'net_worth':     0.12,  # positive
    'tower_damage':  0.05,  # weak positive
    'obs_placed':    0.05,  # weak positive
    'observer_kills': 0.02,
    'camps_stacked':  0.01,
}

STAT_COLS = [
    'gold_per_min', 'xp_per_min', 'hero_damage', 'net_worth',
    'last_hits', 'tower_damage', 'kills', 'teamfight_participation',
    'lane_efficiency_pct', 'stuns', 'obs_placed', 'sen_placed',
    'hero_healing', 'assists', 'camps_stacked', 'observer_kills'
]
MIN_SAMPLES = input('Enter MIN_SAMPLES for stat calculation (leave blank for default 30): ')
if not MIN_SAMPLES:
    MIN_SAMPLES = 30
else:
    MIN_SAMPLES = int(MIN_SAMPLES)

setup_logger(logfile_path='logs/calculate_rating.log')
log = logging.getLogger(__name__)
db = DotaDB(schema='public', local=True)
NUMERATOR = input('Enter TAU numerator for rating model (leave blank for model default 25): ')
DENOMINATOR = input('Enter TAU denominator for rating model (leave blank for model default 300): ')
if not NUMERATOR:
    NUMERATOR = 25
else:
    NUMERATOR = int(NUMERATOR)
if not DENOMINATOR:
    DENOMINATOR = 300
else:
    DENOMINATOR = int(DENOMINATOR)
TAU = float(NUMERATOR / DENOMINATOR)
model = PlackettLuce(tau=TAU)

player_ratings = {}
rating_history = []
draft_strengths = []
hero_patch_stats = None
hero_stats = None
patch_stats = None
global_stats = None
baseline_cache = {}

hero_winrates = None
hero_synergy = None
hero_counters = None

def main():
    log.info(
        f'Starting to calculating ratings for chosen values: \n \
            MIN_SAMPLES: {MIN_SAMPLES} \n \
            TAU NUMERATOR: {NUMERATOR} \n \
            TAU DENOMINATOR: {DENOMINATOR}'
        )
    log.info("Precomputing hero baselines...")
    global hero_patch_stats, hero_stats, patch_stats, global_stats, baseline_cache
    hero_patch_stats, hero_stats, patch_stats, global_stats = compute_hero_stats(db)
    global hero_winrates, hero_synergy, hero_counters 
    hero_winrates, hero_synergy, hero_counters = compute_draft_features(db)
    for (hero_id, patch), row in hero_patch_stats.iterrows():
        for col in STAT_COLS:
            count = row[(col, 'count')]
            if count >= MIN_SAMPLES:
                mean = row[(col, 'mean')]
                std  = row[(col, 'std')]
                if pd.notna(mean) and pd.notna(std) and std > 0:
                    baseline_cache[(hero_id, patch, col)] = (mean, std)
    log.info("Loading metadata...")
    metadata = db.query_select_to_df('SELECT * FROM main_metadata', table='main_metadata')
    metadata['start_date_time'] = pd.to_datetime(metadata['start_date_time'])
    metadata = metadata.sort_values(by='start_date_time').reset_index(drop=True)

    # Build lookup dicts from metadata
    radiant_win_lookup = dict(zip(metadata['match_id'], metadata['radiant_win']))


    # Get match IDs that have player data, sorted chronologically
    match_ids_with_players = [
        mid[0] for mid in db.query_select(
            '''SELECT DISTINCT pms.match_id, mm.start_date_time 
               FROM player_match_stats pms
               JOIN main_metadata mm ON mm.match_id = pms.match_id
               ORDER BY mm.start_date_time ASC'''
        )
    ]
    log.info(f"{len(match_ids_with_players):,} matches have player data.")

    BATCH_SIZE = 1000
    total = len(match_ids_with_players)
    for i in range(0, total, BATCH_SIZE):
        batch = match_ids_with_players[i:i + BATCH_SIZE]
        players_df = db.query_select_to_df(
            'SELECT * FROM player_match_stats WHERE match_id = ANY(%s)',
            params=(batch,),
            table='player_match_stats'
        )
        for match_id, group in players_df.groupby('match_id'):
            radiant_win = radiant_win_lookup.get(match_id)

            if radiant_win is None:
                print(f"Match {match_id} not found in metadata, skipping.")
                continue

            process_match_with_players(match_id, group, radiant_win)

        log.info(f"Processed {min(i + BATCH_SIZE, total):,} / {total:,} matches...")

    log.info("Saving results...")

    final_ratings = pd.DataFrame([
        {
            'account_id': pid,
            'mu':         r.mu,
            'sigma':      r.sigma,
            'ordinal':    r.ordinal(),
        }
        for pid, r in player_ratings.items()
        if not isinstance(pid, str)
    ]).sort_values('ordinal', ascending=False)

    history_df = pd.DataFrame(rating_history)
    drafts_df = pd.DataFrame(draft_strengths)

    final_ratings.to_csv(f'data/player_ratings_{MIN_SAMPLES}_{NUMERATOR}_{DENOMINATOR}.csv', index=False)
    history_df.to_csv(f'data/rating_history_{MIN_SAMPLES}_{NUMERATOR}_{DENOMINATOR}.csv', index=False)
    drafts_df.to_csv('data/draft_strength.csv')

    log.info(f"Done. Rated {len(final_ratings):,} unique players.")
    log.info(f"Rating history: {len(history_df):,} entries.")

def compute_hero_stats(db: DotaDB):
    """
    Precompute mean/std per stat at three levels of granularity.
    Called once before the rating pipeline runs.
    """
    print("Loading player stats for hero baseline computation...")
    df = db.query_select_to_df(
        f'''SELECT hero_id, patch, {', '.join(STAT_COLS)}
            FROM player_match_stats
            WHERE hero_id IS NOT NULL
            AND patch IS NOT NULL''',
            columns=['hero_id', 'patch'] + STAT_COLS
    )

    # Level 1 — hero + patch (most specific)
    hero_patch_stats = df.groupby(['hero_id', 'patch'])[STAT_COLS].agg(['mean', 'std', 'count'])

    # Level 2 — hero only (fallback when patch has too few samples)
    hero_stats = df.groupby('hero_id')[STAT_COLS].agg(['mean', 'std', 'count'])

    # Level 3 — patch only (fallback for unknown heroes)
    patch_stats = df.groupby('patch')[STAT_COLS].agg(['mean', 'std'])

    # Level 4 — global (last resort)
    global_stats = df[STAT_COLS].agg(['mean', 'std'])

    print(f"Hero/patch combinations: {len(hero_patch_stats)}")
    print(f"Unique heroes: {len(hero_stats)}")
    print(f"Unique patches: {len(patch_stats)}")

    return (hero_patch_stats, hero_stats, patch_stats, global_stats)

def get_stat_baseline(col, hero_id, patch):
    """
    Returns (mean, std) for a stat using the most specific available baseline.
    Fallback chain: hero+patch → hero → patch → global
    """
    result = baseline_cache.get((hero_id, patch, col))
    if result:
        return result

    # Level 2 — hero only
    if hero_id in hero_stats.index:
        count = hero_stats.loc[hero_id, (col, 'count')]
        if count >= MIN_SAMPLES:
            mean = hero_stats.loc[hero_id, (col, 'mean')]
            std  = hero_stats.loc[hero_id, (col, 'std')]
            if pd.notna(mean) and pd.notna(std) and std > 0:
                return mean, std

    # Level 3 — patch only
    if patch in patch_stats.index:
        mean = patch_stats.loc[patch, (col, 'mean')]
        std  = patch_stats.loc[patch, (col, 'std')]
        if pd.notna(mean) and pd.notna(std) and std > 0:
            return mean, std

    # Level 4 — global fallback
    mean = global_stats.loc['mean', col]
    std  = global_stats.loc['std', col]
    if pd.notna(mean) and pd.notna(std) and std > 0:
        return mean, std

    return None, None

def get_rating(account_id):
    if account_id not in player_ratings:
        player_ratings[account_id] = model.rating()
    return player_ratings[account_id]

def get_ids(team_df, match_id):
    ids = []
    for _, row in team_df.iterrows():
        aid = row.get('account_id')
        if pd.isna(aid) or aid <= 0:
            ids.append(f'anon_{match_id}_{row["player_slot"]}')
        else:
            ids.append(int(aid))
    return ids

def performance_score(row):
    role    = row.get('inferred_role', 'core')
    weights = SUPPORT_WEIGHTS if role == 'support' else CORE_WEIGHTS
    hero_id = row.get('hero_id')
    patch   = row.get('patch')

    score = total_w = 0.0
    for col, w in weights.items():
        val = row.get(col, np.nan)
        if pd.isna(val):
            continue

        mean, std = get_stat_baseline(
            col, hero_id, patch,
        )
        if mean is None:
            continue

        z          = (val - mean) / std
        normalised = 1 / (1 + np.exp(-z))
        score     += w * normalised
        total_w   += w

    return score / total_w if total_w > 0 else 0.3

def assign_roles(team_df):
    """
    Assigns 'support' or 'core' role per player based on last_hits rank within the match.
    The two players with the lowest last_hits are classified as supports.
    Returns the dataframe with a new 'inferred_role' column.
    """
    df = team_df.copy()
    lh_rank = df['last_hits'].rank(method='first', ascending=True)
    df['inferred_role'] = lh_rank.apply(lambda r: 'support' if r <= 2 else 'core')
    return df

def get_team_weights(team_df):
    scores = [performance_score(row) for _, row in team_df.iterrows()]
    total = sum(scores)
    if total == 0:
        return [1 / len(scores)] * len(scores)
    return [s / total for s in scores]

def compute_draft_features(db: DotaDB):
    query = '''
        SELECT
            hero_id,
            patch,
            AVG(win) AS winrate,
            COUNT(*)
        FROM player_match_stats
        GROUP BY hero_id, patch
        HAVING COUNT(*) >= 20
        '''
    hero_winrates = db.query_select_to_df(query, columns=['hero_id', 'patch', 'winrate', 'match_count'])
    query = '''
        SELECT 
            LEAST(mp1.hero_id, mp2.hero_id)    as hero1,
            GREATEST(mp1.hero_id, mp2.hero_id) as hero2,
            AVG(mp1.win) as pair_winrate,
            COUNT(*) 
        FROM player_match_stats mp1
        JOIN player_match_stats mp2 
            ON mp1.match_id = mp2.match_id
            AND mp1.hero_id < mp2.hero_id
            AND mp1.is_radiant = mp2.is_radiant
        GROUP BY 1, 2
        HAVING COUNT(*) >= 20
        '''
    hero_synergy = db.query_select_to_df(query, columns=['hero_id1', 'hero_id2', 'pair_winrate', 'match_count'])
    query = '''
        SELECT 
            mp1.hero_id as hero_id,
            mp2.hero_id as enemy_hero_id,
            AVG(mp1.win) as winrate_vs,
            COUNT(*) as games
        FROM player_match_stats mp1
        JOIN player_match_stats mp2
            ON mp1.match_id = mp2.match_id
            AND mp1.is_radiant != mp2.is_radiant
        GROUP BY 1, 2
        HAVING COUNT(*) >= 20
        '''
    hero_counters = db.query_select_to_df(query, columns=['hero_id', 'enemy_hero_id', 'winrate_vs', 'match_count'])
    hero_winrates['winrate']      = hero_winrates['winrate'].astype(float)
    hero_synergy['pair_winrate']  = hero_synergy['pair_winrate'].astype(float)
    hero_counters['winrate_vs']   = hero_counters['winrate_vs'].astype(float)
    return hero_winrates, hero_synergy, hero_counters

def calculate_draft_strength(team_heroes, enemy_heroes, patch,
                   hero_winrates, hero_synergy, hero_counters):
    """
    Compute a draft strength score for a team given their heroes and the enemy heroes.
    Returns a float — higher is stronger draft.

    team_heroes:  list of hero_ids for this team
    enemy_heroes: list of hero_ids for the enemy team
    patch:        current patch int
    """
    # ── 1. Individual hero win rates ─────────────────────────────────────────
    wr_scores = []
    for hero_id in team_heroes:
        # try patch-specific first, fall back to overall
        patch_wr = hero_winrates[
            (hero_winrates['hero_id'] == hero_id) &
            (hero_winrates['patch'] == patch) 
        ]['winrate']

        if len(patch_wr) > 0:
            wr_scores.append(patch_wr.iloc[0])
        else:
            overall_wr = hero_winrates[
                (hero_winrates['hero_id'] == hero_id)
            ]['winrate']
            if len(overall_wr) > 0:
                wr_scores.append(overall_wr.mean())
            else:
                wr_scores.append(0.50)  # unknown hero — assume neutral

    hero_wr_score = np.mean(wr_scores)

    # ── 2. Team synergy — all hero pairs ────────────────────────────────────
    synergy_scores = []
    for i, h1 in enumerate(team_heroes):
        for h2 in team_heroes[i+1:]:
            key_h1 = min(h1, h2)
            key_h2 = max(h1, h2)
            pair = hero_synergy[
                (hero_synergy['hero_id1'] == key_h1) &
                (hero_synergy['hero_id2'] == key_h2) 
            ]['pair_winrate']
            if len(pair) > 0:
                synergy_scores.append(pair.iloc[0])

    synergy_score = np.mean(synergy_scores) if synergy_scores else 0.50

    # ── 3. Counter score — how well this team counters the enemy ────────────
    counter_scores = []
    for hero_id in team_heroes:
        for enemy_id in enemy_heroes:
            matchup = hero_counters[
                (hero_counters['hero_id'] == hero_id) &
                (hero_counters['enemy_hero_id'] == enemy_id) 
            ]['winrate_vs']
            if len(matchup) > 0:
                counter_scores.append(matchup.iloc[0])

    counter_score = np.mean(counter_scores) if counter_scores else 0.50

    # ── Weighted combination ─────────────────────────────────────────────────
    draft_score = (
        hero_wr_score  * 0.40 +
        synergy_score  * 0.35 +
        counter_score  * 0.25
    )
    return draft_score
    
def process_match_with_players(match_id, players_df, radiant_win):
    radiant = assign_roles(players_df[players_df['is_radiant'] == True].copy())
    dire    = assign_roles(players_df[players_df['is_radiant'] == False].copy())

    radiant_heroes = radiant['hero_id'].tolist()
    dire_heroes    = dire['hero_id'].tolist()
    patch          = players_df['patch'].iloc[0]
    radiant_draft = calculate_draft_strength(
        radiant_heroes, dire_heroes, patch,
        hero_winrates, hero_synergy, hero_counters
    )
    dire_draft = calculate_draft_strength(
        dire_heroes, radiant_heroes, patch,
        hero_winrates, hero_synergy, hero_counters
    )

    if len(radiant) == 0 or len(dire) == 0:
        return

    radiant_ids = get_ids(radiant, match_id)
    dire_ids    = get_ids(dire, match_id)

    radiant_ratings = [get_rating(pid) for pid in radiant_ids]
    dire_ratings    = [get_rating(pid) for pid in dire_ids]

    # ── Store PRE-match ratings in history ───────────────────────────────────
    for pid, r in zip(radiant_ids, radiant_ratings):
        if not isinstance(pid, str):
            rating_history.append({
                'account_id': pid,
                'match_id':   match_id,
                'is_radiant': True,
                'mu':         r.mu,
                'sigma':      r.sigma,
                'ordinal':    r.ordinal(),
            })
    for pid, r in zip(dire_ids, dire_ratings):
        if not isinstance(pid, str):
            rating_history.append({
                'account_id': pid,
                'match_id':   match_id,
                'is_radiant': False,
                'mu':         r.mu,
                'sigma':      r.sigma,
                'ordinal':    r.ordinal(),
            })
    
    draft_strengths.append({
        'match_id': match_id,
        'rad_draft_strength': radiant_draft,
        'dire_draft_strength': dire_draft
    })
        
    # Get weights
    radiant_weights, dire_weights = get_team_weights(radiant), get_team_weights(dire)
    if radiant_win:
        new_radiant, new_dire = model.rate(
            [radiant_ratings, dire_ratings],
            weights=[radiant_weights, dire_weights]
        )
    else:
        new_dire, new_radiant = model.rate(
            [dire_ratings, radiant_ratings],
            weights=[dire_weights, radiant_weights]
        )
    for pid, new_r in zip(radiant_ids + dire_ids, new_radiant + new_dire):
        player_ratings[pid] = new_r

if __name__ == '__main__':
    main()