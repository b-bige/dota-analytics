-- Active: 1771411304973@@165.22.73.33@5432@dota@public
CREATE TABLE match_position (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT REFERENCES match_details(id),
    hero_id BIGINT,
    minute SMALLINT,
    position_x INT,
    position_y INT 
);
SELECT COUNT(*) FROM match_details;

SELECT * FROM information_schema.tables WHERE table_schema = 'kaggle';
SELECT DISTINCT ld."displayName" dn
FROM match_details md
    INNER JOIN league_details ld ON md."leagueId" = ld.id;

SELECT 
    id, 
    md."radiantTeamId",
    md."direTeamId",
    md."didRadiantWin",
    md."durationSeconds",
    md."startDateTime"
 FROM match_details md
 INNER JOIN league_details ld
 ON md."leagueId" = ld.id
 WHERE md."startDateTime" > %s AND md."startDateTime" < %s AND ld.id = %s;

 SELECT "durationSeconds" FROM match_details WHERE id = 8299260483;

 SELECT hd.name 
        FROM hero_details hd
        LEFT JOIN match_players mp
        ON mp."heroId" = hd.id
        WHERE mp.match_id = 6323023888;

SELECT * FROM match_players WHERE match_id = 7443838658;

CREATE TABLE match_players_temp AS SELECT DISTINCT ON (match_id, "heroId") * FROM match_players;
SELECT COUNT(*) FROM match_players;
SELECT * FROM match_players_temp WHERE match_id = 8299260483;
SELECT COUNT(*) FROM match_details;
SELECT COUNT(*) FROM match_players_temp; 
    
SELECT 
    hd."shortName", 
    hd."displayName", 
    mp."isRadiant", 
    mp.position,
    mp.networth,
    mp."goldPerMinute",
    mp."heroDamage",
    mp."towerDamage",
    mp."steamAccountId",
    CASE 
        -- TOP LANE: Radiant Offlane (3,4) or Dire Safelane (1,5)
        WHEN (mp."isRadiant" = true AND mp.position IN ('POSITION_3', 'POSITION_4')) OR 
             (mp."isRadiant" = false AND mp.position IN ('POSITION_1', 'POSITION_5')) THEN 1
        -- MID LANE: Position 2
        WHEN mp.position = 'POSITION_2' THEN 2
        -- BOT LANE: Radiant Safelane (1,5) or Dire Offlane (3,4)
        WHEN (mp."isRadiant" = true AND mp.position IN ('POSITION_1', 'POSITION_5')) OR 
             (mp."isRadiant" = false AND mp.position IN ('POSITION_3', 'POSITION_4')) THEN 3
    END as lane_group
FROM hero_details hd
INNER JOIN match_players mp
ON mp."heroId" = hd.id
WHERE mp."match_id" = 6556876576
ORDER BY 
    mp."isRadiant" DESC, -- Radiant players grouped first
    CASE 
        -- Sorting Radiant: Top -> Mid -> Bot
        WHEN mp."isRadiant" = true THEN
            CASE 
                WHEN mp.position IN ('POSITION_3', 'POSITION_4') THEN 1
                WHEN mp.position = 'POSITION_2' THEN 2
                WHEN mp.position IN ('POSITION_1', 'POSITION_5') THEN 3
            END
        -- Sorting Dire: Top -> Mid -> Bot
        ELSE
            CASE 
                WHEN mp.position IN ('POSITION_1', 'POSITION_5') THEN 1
                WHEN mp.position = 'POSITION_2' THEN 2
                WHEN mp.position IN ('POSITION_3', 'POSITION_4') THEN 3
            END
    END ASC,
    -- Final tie-breaker: Ensure Pos 1 is above Pos 5 in the same lane
    mp.position ASC; 

SELECT DISTINCT position FROM match_players;
SELECT * FROM match_players WHERE match_players.name IS NOT NULL;
SELECT COUNT(*) FROM match_players mp WHERE mp."proSteamAccount_name" IS NOT NULL;

SELECT AVG(CAST("didRadiantWin" AS INT)) FROM match_details;

SELECT * FROM match_players WHERE match_id = 7646983904;

SELECT AVG(CAST("didRadiantWin" AS INT)) FROM match_details md WHERE 1=1 AND "leagueId" = 15610 AND md."startDateTime" BETWEEN 1670194800.0 AND 1670367600.0; 

SELECT ld."displayName"
FROM league_details ld
    JOIN match_details md ON ld.id = md."leagueId"
WHERE md."startDateTime" BETWEEN 1670194800.0 AND 1670367600.0;

SELECT * FROM match_details md WHERE 1=1 AND "leagueId" = 13877 AND md."startDateTime" BETWEEN 1639609200.0 AND 1639782000.0;
SELECT * FROM match_details WHERE "leagueId" = 13877 ORDER BY "startDateTime" ASC;

SELECT
    COUNT(*) FILTER (WHERE mpb."isPick" = TRUE) AS pick,
    COUNT(*) FILTER (WHERE mpb."isPick" = FALSE) AS ban,
    hd."displayName"
FROM match_pick_bans mpb
JOIN hero_details hd
ON hd.id = mpb."heroId"
WHERE mpb."heroId" IS NOT NULL 
    AND mpb.match_id = ANY(ARRAY[1, 2, 3])
GROUP BY hd."displayName";

SELECT DISTINCT "radiantTeamId" 
FROM match_details 
UNION 
SELECT DISTINCT "direTeamId" 
FROM match_details;

SELECT COUNT(DISTINCT "radiantTeamId") FROM  match_details;
SELECT COUNT(DISTINCT "direTeamId") FROM  match_details;

SELECT DISTINCT week FROM hero_stats ORDER BY week DESC;

SELECT md.id, md."radiantTeamId", md."direTeamId", md."didRadiantWin", md."durationSeconds", md."startDateTimeHuman"
FROM match_details md
JOIN team_details radiant ON radiant.id = md."radiantTeamId"
JOIN team_details dire ON dire.id = md."direTeamId";

SELECT * FROM team_details td WHERE td.id = 5635538;

SELECT *
        FROM match_details md
        JOIN team_details radiant ON radiant.id = md."radiantTeamId"
        JOIN team_details dire ON dire.id = md."direTeamId"
        JOIN league_details l ON l.id = md."leagueId"
        ORDER BY md."startDateTimeHuman" ASC
        LIMIT 20 OFFSET 85020;

EXPLAIN ANALYZE
SELECT AVG(CAST(mp."isVictory" AS INT)) AS winrate,
    COUNT(*) as picks,
    hd."displayName"
FROM match_players mp
JOIN hero_details hd ON mp."heroId" = hd.id
JOIN match_details md ON mp.match_id = md.id
GROUP BY hd."displayName"
HAVING COUNT(*) >= 10
ORDER BY winrate DESC
LIMIT 5;

EXPLAIN ANALYZE
SELECT
    COUNT(*) FILTER (WHERE mpb."isPick" = FALSE) AS count,
    hd."displayName"
FROM match_pick_bans mpb
JOIN hero_details hd
ON hd.id = mpb."heroId"
JOIN match_details md
ON md.id = mpb.match_id
GROUP BY hd."displayName", hd."shortName"
ORDER BY count DESC
LIMIT 5;

SELECT COUNT(*) FILTER (
            WHERE mpb."isPick" = TRUE
        ) AS picks,
        hd."displayName"
    FROM match_pick_bans mpb
    JOIN hero_details hd ON hd.id = mpb."heroId"
    JOIN match_details md ON md.id = mpb.match_id 
    GROUP BY hd."displayName",
        hd."shortName"
    ORDER BY picks DESC
    LIMIT 5;
WITH top_picked AS (
    SELECT COUNT(*) FILTER (
            WHERE mpb."isPick" = TRUE
        ) AS picks,
        hd."displayName"
    FROM match_pick_bans mpb
    JOIN hero_details hd ON hd.id = mpb."heroId"
    JOIN match_details md ON md.id = mpb.match_id 
    GROUP BY hd."displayName",
        hd."shortName"
    ORDER BY picks DESC
    LIMIT 5
), top_banned AS (
    SELECT COUNT(*) FILTER (
            WHERE mpb."isPick" = FALSE
        ) AS bans,
        hd."displayName"
    FROM match_pick_bans mpb
    JOIN hero_details hd ON hd.id = mpb."heroId"
    JOIN match_details md ON md.id = mpb.match_id 
    GROUP BY hd."displayName",
        hd."shortName"
    ORDER BY bans DESC
    LIMIT 5
)
SELECT * FROM top_picked
UNION
SELECT * FROM top_banned;

SELECT COUNT(*) FILTER (
            WHERE mpb."isPick" = FALSE
        ) AS bans,
        hd."displayName"
    FROM match_pick_bans mpb
    JOIN hero_details hd ON hd.id = mpb."heroId"
    JOIN match_details md ON md.id = mpb.match_id 
    GROUP BY hd."displayName",
        hd."shortName"
    ORDER BY bans DESC
    LIMIT 5;

SELECT * FROM hero_pick_ban_stats;

SELECT
            COUNT(*),
        AVG(CAST("didRadiantWin" AS INT)),
        AVG("durationSeconds")

            FROM match_details md
            LEFT JOIN league_details ld ON md."leagueId" = ld.id LEFT JOIN patches p ON md."gameVersionId" = p.id
            WHERE 1=1 AND ld."displayName" = 'DreamLeague Season 26' AND p.name = '7.39' AND md."startDateTimeHuman" BETWEEN 2025-05-30 AND %s

SELECT * FROM team_details WHERE "isPro" = 't';

--TODO Separate tables more

