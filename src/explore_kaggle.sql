-- Active: 1771411304973@@165.22.73.33@5432@dota@kaggle
SELECT match_id, start_date_time FROM main_metadata WHERE start_date_time > '2021-12-15 14:45:00' ORDER BY start_date_time ASC;
-- Matches where stratz has detailed data (at least I have found this to be the point, might not be because it seems weird)
SELECT COUNT(*) FROM main_metadata;
SELECT DISTINCT match_id FROM main_metadata; 

SELECT * FROM main_metadata;
SELECT * FROM picks_bans WHERE match_id = 2049344492;
ALTER TABLE main_metadata ADD CONSTRAINT pk_main_metadata_match_id PRIMARY KEY(match_id);

SELECT * FROM main_metadata WHERE match_id = 6326723311;

