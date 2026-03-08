CREATE MATERIALIZED VIEW hero_pick_ban_stats AS
SELECT
    COUNT(*) FILTER (WHERE mpb."isPick" = TRUE) AS picks,
    COUNT(*) FILTER (WHERE mpb."isPick" = FALSE) AS bans,
    hd."displayName"
FROM match_pick_bans mpb
JOIN hero_details hd ON hd.id = mpb."heroId"
GROUP BY hd."displayName", hd."shortName";
CREATE INDEX idx_mv_picks ON hero_pick_ban_stats(picks DESC);
CREATE INDEX idx_mv_bans ON hero_pick_ban_stats(bans DESC);

CREATE MATERIALIZED VIEW hero_winrate_stats AS
SELECT 
    AVG(CAST(mp."isVictory" AS INT)) AS winrate,
    COUNT(*) AS picks,
    hd."displayName"
FROM match_players mp
JOIN hero_details hd ON mp."heroId" = hd.id
JOIN match_details md ON mp.match_id = md.id
GROUP BY hd."displayName";

CREATE INDEX idx_mv_winrate ON hero_winrate_stats(winrate DESC);
CREATE INDEX idx_mv_hero_picks ON hero_winrate_stats(picks);