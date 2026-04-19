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

CREATE MATERIALIZED VIEW hero_synergy_stats AS
SELECT 
    LEAST(mp1."heroId", mp2."heroId")       AS hero1,
    GREATEST(mp1."heroId", mp2."heroId")    AS hero2,
    AVG(CAST(mp1."isVictory" AS INT))       AS winrate,
    COUNT(*)                                AS games
FROM match_players mp1
JOIN match_players mp2 
    ON  mp1.match_id   = mp2.match_id
    AND mp1."heroId"   < mp2."heroId"
    AND mp1."isRadiant" = mp2."isRadiant"
GROUP BY 1, 2
HAVING COUNT(*) >= 20;

CREATE MATERIALIZED VIEW hero_counter_stats AS 
SELECT 
    mp1."heroId"                            AS hero_id,
    mp2."heroId"                            AS enemy_id,
    AVG(CAST(mp1."isVictory" AS INT))       AS winrate,
    COUNT(*)                                AS games
FROM match_players mp1
JOIN match_players mp2
    ON  mp1.match_id    = mp2.match_id
    AND mp1."isRadiant" != mp2."isRadiant"
GROUP BY 1, 2
HAVING COUNT(*) >= 20;

SELECT * FROM current_player_ratings;