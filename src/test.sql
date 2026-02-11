-- Active: 1765906160049@@localhost@5432@dota
SELECT * FROM matches;
SELECT COUNT(*) FROM matches;
SELECT COUNT(tier), tier FROM leagues GROUP BY tier;
SELECT * FROM leagues WHERE tier = 'premium';

SELECT * FROM leagues WHERE leagueid = 18660;
BEGIN;

ROLLBACK;

SELECT * FROM leagues WHERE name LIKE '%FISSURE%';

SELECT * FROM leagues;

SELECT COUNT(*) FROM matches WHERE start_date >= '2025-03-01 00:00:00';

SELECT COUNT(*) FROM matches;
SELECT DISTINCT leagueid FROM leagues;

SELECT * FROM patches;

SELECT * FROM npcs WHERE id=17;

SELECT * FROM heroes;

SELECT * FROM match_win_rates;

SELECT * FROM match_players;

SELECT * FROM match_runes;
SELECT DISTINCT * FROM match_details WHERE id=8187923027;

SELECT COUNT(DISTINCT match_id) FROM match_leads;

SELECT DISTINCT variant FROM match_players;

SELECT pg_size_pretty(pg_database_size('dota'));

SELECT * FROM information_schema.tables;

SELECT * FROM matches WHERE start_date >= '2025-02-21 00:00:00';
SELECT COUNT(id) FROM match_details;

SELECT COUNT(start_date) FROM matches WHERE start_date >= '2025-02-21 00:00:00';

SELECT * FROM match_players;

SELECT roles FROM heroes;

SELECT * FROM patches;

SELECT * FROM item_details WHERE id = 16;

SELECT id, localized_name FROM heroes;

SELECT id, localized_name FROM heroes WHERE localized_name = 'Invoker';

SELECT id, localized_name FROM heroes WHERE id = 42;

SELECT * FROM hero_stats;

SELECT * FROM matchup_with;


SELECT COUNT(DISTINCT week) FROM matchup_lane_outcome;

SELECT DISTINCT week FROM hero_item_full_purchase ORDER BY week;

SELECT * FROM heroes WHERE id = 64;
SELECT DISTINCT mp."heroId", heroes.localized_name 
FROM match_players mp
INNER JOIN heroes
ON mp."heroId" = heroes.id
WHERE mp.variant BETWEEN 3 AND 7;

SELECT * FROM hero_facets WHERE "abilityId" = 1281;

SELECT COUNT(DISTINCT "heroId") FROM hero_facets;

SELECT * FROM ability_details;

SELECT * FROM match_players WHERE match_id = 8183642521;

SELECT COUNT(DISTINCT match_id) FROM match_players WHERE steam_account_id IS NOT NULL;
SELECT * FROM match_details WHERE match_details."radiantTeamId" = 8261500 ORDER BY "startDateTime" DESC;

SELECT column_name FROM information_schema.columns WHERE table_name = 'match_details';

SELECT * FROM match_details WHERE match_details."radiantTeamId" = 8261500;