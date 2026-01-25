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

SELECT * FROM matches;

SELECT DISTINCT leagueid FROM leagues;

SELECT * FROM patches;

SELECT * FROM heroes;
