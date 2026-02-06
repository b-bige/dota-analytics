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

SELECT COUNT(*) FROM matches;
SELECT COUNT(id) FROM match_details;

SELECT COUNT(start_date) FROM matches WHERE start_date >= '2025-02-21 00:00:00';

SELECT * FROM match_players;

