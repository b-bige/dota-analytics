-- Active: 1771411304973@@165.22.73.33@5432@dota@public
CREATE MATERIALIZED VIEW hero_pick_ban_stats AS
SELECT
    COUNT(*) FILTER (WHERE mpb."isPick" = TRUE) AS picks,
    COUNT(*) FILTER (WHERE mpb."isPick" = FALSE) AS bans,
    hd."displayName"
FROM match_pick_bans mpb
JOIN hero_details hd ON hd.id = mpb."heroId"
GROUP BY hd."displayName", hd."shortName";
CREATE MATERIALIZED VIEW hero_winrate_stats AS
SELECT 
    AVG(CAST(mp."isVictory" AS INT)) AS winrate,
    COUNT(*) AS picks,
    hd."displayName"
FROM match_players mp
JOIN hero_details hd ON mp."heroId" = hd.id
JOIN match_details md ON mp.match_id = md.id
GROUP BY hd."displayName";
CREATE MATERIALIZED VIEW hero_presence_stats AS
SELECT
    COUNT(*) AS presence,
    hd."displayName"
FROM match_pick_bans mpb
JOIN hero_details hd ON hd.id = mpb."heroId"
GROUP BY hd."displayName", hd."shortName";
CREATE MATERIALIZED VIEW mv_match_networth_shares AS
SELECT 
    mp.match_id,
    mp.position,
    mp.networth,
    mp."isRadiant",
    mp."isVictory",
    (CAST(mp.networth AS FLOAT) / tn.total_networth) AS networth_share
FROM match_players mp
JOIN (
    SELECT 
        match_id,
        "isRadiant",
        SUM(networth) AS total_networth
    FROM match_players
    WHERE networth IS NOT NULL
    GROUP BY match_id, "isRadiant"
) tn ON mp.match_id = tn.match_id AND mp."isRadiant" = tn."isRadiant"
WHERE mp.position IS NOT NULL;

CREATE MATERIALIZED VIEW hero_patch_stats AS
-- Patch-specific win
(SELECT 
    mp."heroId" AS hero_id,
    md."gameVersionId" AS patch,
    SUM(CASE WHEN mp."isVictory" THEN 1 ELSE 0 END) AS wins,
    COUNT(*) AS games
FROM match_players mp
JOIN match_details md ON mp.match_id = md.id
GROUP BY 1, 2)
UNION ALL
-- Global win
(SELECT 
    mp."heroId" AS hero_id,
    0 AS patch,
    SUM(CASE WHEN mp."isVictory" THEN 1 ELSE 0 END) AS wins,
    COUNT(*) AS games
FROM match_players mp
GROUP BY 1, 2);

CREATE MATERIALIZED VIEW hero_synergy_stats AS
-- Patch-Specific Synergy
SELECT 
    md."gameVersionId" AS patch,
    LEAST(mp1."heroId", mp2."heroId") AS hero_a,
    GREATEST(mp1."heroId", mp2."heroId") AS hero_b,
    SUM(CASE WHEN mp1."isVictory" THEN 1 ELSE 0 END) AS wins,
    COUNT(*) AS games
FROM match_players mp1
JOIN match_players mp2 ON mp1.match_id = mp2.match_id
JOIN match_details md ON mp1.match_id = md.id
WHERE mp1."heroId" < mp2."heroId" AND mp1."isRadiant" = mp2."isRadiant"
GROUP BY 1, 2, 3
UNION ALL
-- Global Synergy
(SELECT 
    0 AS patch,
    LEAST(mp1."heroId", mp2."heroId") AS hero_a,
    GREATEST(mp1."heroId", mp2."heroId") AS hero_b,
    SUM(CASE WHEN mp1."isVictory" THEN 1 ELSE 0 END) AS wins,
    COUNT(*) AS games
FROM match_players mp1
JOIN match_players mp2 ON mp1.match_id = mp2.match_id
WHERE mp1."heroId" < mp2."heroId" AND mp1."isRadiant" = mp2."isRadiant"
GROUP BY 1, 2, 3);

CREATE MATERIALIZED VIEW hero_counter_stats AS 
SELECT 
    md."gameVersionId" AS patch,
    mp1."heroId" AS hero_id,
    mp2."heroId" AS enemy_id,
    SUM(CASE WHEN mp1."isVictory" THEN 1 ELSE 0 END) AS wins,
    COUNT(*) AS games
FROM match_players mp1
JOIN match_players mp2 ON mp1.match_id = mp2.match_id
JOIN match_details md ON mp1.match_id = md.id
WHERE mp1."isRadiant" != mp2."isRadiant"
GROUP BY 1, 2, 3
HAVING COUNT(*) >= 5;

CREATE MATERIALIZED VIEW hero_counter_stats AS 
-- Patch-Specific Counters
(SELECT 
    md."gameVersionId" AS patch,
    mp1."heroId" AS hero_id,
    mp2."heroId" AS enemy_id,
    SUM(CASE WHEN mp1."isVictory" THEN 1 ELSE 0 END) AS wins,
    COUNT(*) AS games
FROM match_players mp1
JOIN match_players mp2 ON mp1.match_id = mp2.match_id
JOIN match_details md ON mp1.match_id = md.id
WHERE mp1."isRadiant" != mp2."isRadiant"
GROUP BY 1, 2, 3)

UNION ALL
-- Global Counters
(SELECT 
    0 AS patch,
    mp1."heroId" AS hero_id,
    mp2."heroId" AS enemy_id,
    SUM(CASE WHEN mp1."isVictory" THEN 1 ELSE 0 END) AS wins,
    COUNT(*) AS games
FROM match_players mp1
JOIN match_players mp2 ON mp1.match_id = mp2.match_id
WHERE mp1."isRadiant" != mp2."isRadiant"
GROUP BY 1, 2, 3);

SELECT 
md.id, md."radiantTeamId", md."direTeamId",
md."didRadiantWin", md."durationSeconds", md."startDateTimeHuman",
radiant.name, dire.name, radiant.logo, dire.logo, ld."displayName", 
md.avg_radiant_rating, md.avg_dire_rating, 
md.radiant_draft_score, md.dire_draft_score

FROM match_details md
LEFT JOIN patches p ON md."gameVersionId" = p.id LEFT JOIN league_details ld ON md."leagueId" = ld.id LEFT JOIN team_details radiant ON radiant.id = md."radiantTeamId" LEFT JOIN team_details dire ON dire.id = md."direTeamId"
WHERE 1=1 AND (p.name = ANY(:value)) AND (ld."displayName" = ANY(:value))

ORDER BY md."startDateTimeHuman" DESC LIMIT :page_size OFFSET :offset
         {'value': ['ESL One Fall 2021 powered by Intel'], 'page_size': 20, 'offset': 0};