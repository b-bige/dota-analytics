-- Active: 1771411304973@@165.22.73.33@5432@dota@public
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

SELECT * FROM match_players WHERE match_players."steamAccountId" IS NOT NULL;

SELECT DISTINCT match_id FROM match_players mp WHERE mp."steamAccountId" IS NOT NULL;

SELECT DISTINCT match_id FROM match_players mp WHERE mp."steamAccountId" IS NULL;

SELECT * FROM match_details;

SELECT DISTINCT md."leagueId" FROm match_details md;
SELECT * FROM league_details ld;

SELECT id, ld."displayName", ld."tournamentUrl", ld."prizePool", ld."basePrizePool", ld."startDateTime"
FROM league_details ld 
WHERE ld."prizePool" > 500000
ORDER BY "startDateTime" DESC;

SELECT * FROM match_players WHERE match_id = 8461735141

SELECT * FROM match_details;

SELECT DISTINCT md."radiantTeamId" FROM match_details md;

SELECT DISTINCT md."direTeamId" FROM match_details md;

SELECT * FROM league_details ld WHERE ld."displayName" LIKE 'ESL%' AND ld."prizePool" <> 0;
SELECT * FROM league_details ld WHERE ld."displayName" LIKE '%DreamLeague%' AND ld."prizePool" <> 0;

SELECT * FROM league_details ld WHERE ld."displayName" LIKE '%International%' AND ld."prizePool" <> 0;

SELECT * FROM league_details ld WHERE ld."displayName" LIKE 'FISSURE%' AND ld."displayName" NOT LIKE '%Special' AND ld."prizePool" <> 0;

SELECT * FROM league_details ld WHERE ld."displayName" LIKE '%Clavision%' AND ld."prizePool" <> 0;

SELECT * FROM match_details md INNER JOIN league_details ld ON md."leagueId" = ld.id WHERE ld."displayName" LIKE '%Clavision%'; 

SELECT * FROM patches;

SELECT * FROM match_predicted_win_rates;

ALTER TABLE match_imp_per_minute ADD COLUMN minute SMALLINT;

SELECT ms.*, mtu.*, mo.* FROM match_snapshots ms 
INNER JOIN match_tower_updates mtu
ON ms.snapshot_id = mtu.snapshot_id
INNER JOIN match_outpost_updates mo 
ON ms.snapshot_id = mo.snapshot_id
WHERE ms.match_id = 8183642521;

SELECT * FROM match_details WHERE id = 8183642521; 

SELECT mtu.* FROM match_tower_updates mtu 
INNER JOIN match_snapshots
ON match_snapshots.snapshot_id = mtu.snapshot_id
WHERE match_snapshots.match_id = 8183642521;

SELECT mou.* FROM match_outpost_updates mou 
INNER JOIN match_snapshots
ON match_snapshots.snapshot_id = mou.snapshot_id
WHERE match_snapshots.match_id = 8183642521;

SELECT * FROM match_snapshots WHERE match_id = 8183642521;

SELECT * FROM match_outpost_updates;

SELECT * FROM match_farm WHERE source_type = 'buybackGold';

CREATE DATABASE vejle_parking;

SELECT * FROM match_farm;

SELECT * FROM league_details ld WHERE ld."prizePool" > 50000 ORDER BY ld."startDateTime" ASC;

SELECT md.* FROM match_details md WHERE md."leagueId" in (17795, 17509);