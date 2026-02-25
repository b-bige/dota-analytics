-- Active: 1771411304973@@165.22.73.33@5432@dota@public
CREATE SCHEMA kaggle;

SELECT pg_size_pretty(pg_database_size('dota'));

SELECT * FROM item_details;