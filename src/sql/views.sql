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