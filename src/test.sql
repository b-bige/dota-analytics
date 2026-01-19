-- Active: 1765906160049@@localhost@5432@dota
SELECT * FROM matches;
SELECT COUNT(*) FROM matches;
SELECT COUNT(tier), tier FROM leagues GROUP BY tier;
SELECT * FROM leagues WHERE tier = 'premium';

SELECT * FROM leagues WHERE leagueid = 18660;
BEGIN;

ROLLBACK;