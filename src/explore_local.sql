-- Active: 1773752737738@@127.0.0.1@5432@dota@public
SELECT COUNT(DISTINCT match_id) FROM player_match_stats;

SELECT start_date_time FROM main_metadata ORDER BY start_date_time ASC;

SELECT COUNT(*) FROM main_metadata WHERE dire_team_id IS NULL;

SELECT match_id FROM main_metadata WHERE start_date_time > '2021-01-01'

SELECT * FROM player_match_stats WHERE match_id = 5775166584 AND is_radiant = TRUE;

SELECT DISTINCT pms.match_id, mm.start_date_time 
    FROM player_match_stats pms
    JOIN main_metadata mm ON mm.match_id = pms.match_id
    ORDER BY mm.start_date_time ASC;

SELECT
    hero_id,
    patch,
    AVG(win) AS winrate,
    COUNT(*)
FROM player_match_stats
GROUP BY hero_id, patch
HAVING COUNT(*) >= 20;

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
HAVING COUNT(*) >= 20;

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
HAVING COUNT(*) >= 20;