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

SELECT MAX("durationSeconds") / 60 FROM match_details;
SELECT "durationSeconds" / 60 AS mins 
FROM match_details
WHERE "durationSeconds" / 60 > 90;

SELECT 
    CASE 
        WHEN "durationSeconds" < 25 * 60                          THEN '< 25 min'
        WHEN "durationSeconds" BETWEEN 25 * 60 AND 45 * 60 - 1   THEN '25 - 45 min'
        WHEN "durationSeconds" BETWEEN 45 * 60 AND 60 * 60 - 1   THEN '45 - 60 min'
        WHEN "durationSeconds" BETWEEN 60 * 60 AND 85 * 60 - 1   THEN '60 - 90 min'
        ELSE                                                            '> 80 min'
    END AS bucket,
    COUNT(*) AS games
FROM match_details
GROUP BY bucket
ORDER BY MIN("durationSeconds");

SELECT MAX("durationSeconds") FROM match_details;

SELECT 
    h1."displayName" AS hero1,
    h2."displayName" AS hero2,
    COUNT(*) AS times_together,
    AVG(CAST(mp1."isVictory" AS INT)) AS winrate
FROM match_players mp1
JOIN match_players mp2 
    ON mp1.match_id = mp2.match_id 
    AND mp1."heroId" < mp2."heroId"  -- avoid duplicates
    AND mp1."isRadiant" = mp2."isRadiant"  -- same team
JOIN hero_details h1 ON mp1."heroId" = h1.id
JOIN hero_details h2 ON mp2."heroId" = h2.id
GROUP BY h1."displayName", h2."displayName"
HAVING COUNT(*) >= 10
ORDER BY winrate DESC
LIMIT 10;

SELECT 
    hd1."displayName" AS hero1,
    hd2."displayName" AS hero2,
    mp1.position AS pos1,
    mp2.position AS pos2,
    COUNT(*) AS times_together,
    ROUND(AVG(CAST(mp1."isVictory" AS INT)) * 100, 2) AS winrate
FROM match_players mp1
JOIN match_players mp2 
    ON mp1.match_id = mp2.match_id 
    AND mp1."heroId" < mp2."heroId"
    AND mp1."isRadiant" = mp2."isRadiant"
JOIN hero_details hd1 ON mp1."heroId" = hd1.id
JOIN hero_details hd2 ON mp2."heroId" = hd2.id
WHERE mp1.position = 'POSITION_1' AND mp2.position = 'POSITION_5'  
GROUP BY hd1."displayName", hd2."displayName", mp1.position, mp2.position
HAVING COUNT(*) >= 15
ORDER BY winrate DESC
LIMIT 10;

SELECT 
    hd1."displayName" AS hero1,
    hd2."displayName" AS hero2,
    mp1.position AS pos1,
    mp2.position AS pos2,
    COUNT(*) AS times_together,
    ROUND(AVG(CAST(mp1."isVictory" AS INT)) * 100, 2) AS winrate
FROM match_players mp1
JOIN match_players mp2 
    ON mp1.match_id = mp2.match_id 
    AND mp1."heroId" < mp2."heroId"
    AND mp1."isRadiant" = mp2."isRadiant"
JOIN hero_details hd1 ON mp1."heroId" = hd1.id
JOIN hero_details hd2 ON mp2."heroId" = hd2.id
JOIN match_details md ON mp1.match_id = md.id
WHERE mp1.position = 'POSITION_3' AND mp2.position = 'POSITION_4' AND md."startDateTimeHuman" > '2025-02-01' 
GROUP BY hd1."displayName", hd2."displayName", mp1.position, mp2.position
HAVING COUNT(*) >= 20
ORDER BY times_together DESC
LIMIT 50;

SELECT COUNT(DISTINCT match_id) FROM match_pick_bans mpb
JOIN match_details md on md.id = mpb.match_id;

SELECT * FROM hero_details WHERE id = 85;
SELECT * FROM match_details WHERE id = 6321751509;

SELECT * FROM match_details WHERE avg_radiant_rating IS NULL;

SELECT DISTINCT "seriesId" FROM match_details;
SELECT * FROM match_details WHERE "seriesId" = 737586;
SELECT AVG(CAST("didRadiantWin" AS INT)) FROM match_details WHERE avg_radiant_rating > avg_dire_rating;
SELECT 1 - AVG(CAST("didRadiantWin" AS INT)) FROM match_details WHERE avg_dire_rating > avg_radiant_rating;

SELECT 
    COUNT(*) as total,
    COUNT(avg_radiant_rating) as with_ratings,
    COUNT(*) - COUNT(avg_radiant_rating) as without_ratings
FROM match_details;
SELECT 
    percentile_cont(0.25) WITHIN GROUP (ORDER BY ABS(avg_radiant_rating - avg_dire_rating)) as p25,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY ABS(avg_radiant_rating - avg_dire_rating)) as p50,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY ABS(avg_radiant_rating - avg_dire_rating)) as p75
FROM match_details
WHERE avg_radiant_rating IS NOT NULL;

SELECT 
    AVG(avg_radiant_rating - avg_dire_rating) as mean_diff,
    STDDEV(avg_radiant_rating - avg_dire_rating) as std_diff
FROM match_details
WHERE avg_radiant_rating IS NOT NULL;

SELECT 
    CASE 
        WHEN ABS(avg_radiant_rating - avg_dire_rating) < 5   THEN '0-5'
        WHEN ABS(avg_radiant_rating - avg_dire_rating) < 10  THEN '5-10'
        WHEN ABS(avg_radiant_rating - avg_dire_rating) < 20  THEN '10-20'
        ELSE '20+'
    END as diff_bucket,
    AVG(CAST("didRadiantWin" AS INT)) FILTER (WHERE avg_radiant_rating > avg_dire_rating) as accuracy,
    COUNT(*) as matches
FROM match_details
WHERE avg_radiant_rating IS NOT NULL
GROUP BY 1
ORDER BY 1;

SELECT 
    mp."heroId" as hero_id,
    md."gameVersionId",
    AVG(CAST(mp."isVictory" AS INT)) as winrate,
    COUNT(*) 
FROM match_players mp
JOIN match_details md ON md.id = mp.match_id
GROUP BY mp."heroId", md."gameVersionId"
HAVING COUNT(*) >= 20
ORDER BY winrate DESC;

SELECT 
    LEAST(mp1."heroId", mp2."heroId")    as hero1,
    GREATEST(mp1."heroId", mp2."heroId") as hero2,
    AVG(CAST(mp1."isVictory" AS INT))    as pair_winrate,
    COUNT(*)                            
FROM match_players mp1
JOIN match_players mp2 
    ON mp1.match_id = mp2.match_id
    AND mp1."heroId" < mp2."heroId"
    AND mp1."isRadiant" = mp2."isRadiant"
GROUP BY 1, 2
HAVING COUNT(*) >= 15
ORDER BY pair_winrate DESC;

SELECT 
    mp1."heroId" as hero_id,
    mp2."heroId" as enemy_hero_id,
    AVG(CAST(mp1."isVictory" AS INT)) as winrate_vs,
    COUNT(*) 
FROM match_players mp1
JOIN match_players mp2
    ON mp1.match_id = mp2.match_id
    AND mp1."isRadiant" != mp2."isRadiant"
GROUP BY 1, 2
HAVING COUNT(*) >= 15;

SELECT MIN("startDateTimeHuman") FROM match_details;

SELECT AVG(CAST(("didRadiantWin" = predicted_radiant_win) AS INT)) AS correct
FROM match_details;

--TODO Separate tables more

