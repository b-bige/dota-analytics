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