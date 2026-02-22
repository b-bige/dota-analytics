-- Active: 1771411304973@@165.22.73.33@5432@dota@public
SELECT md.id, md."didRadiantWin", mp."heroId", mp."isRadiant", mp."isVictory" 
FROM match_details md
INNER JOIN match_players mp
ON md.id = mp.match_id;

BEGIN;
DELETE FROM match_details WHERE id IN (
    SELECT match_id FROM (
        SELECT DISTINCT match_id, COUNT(*) AS duplicates
        FROM match_pick_bans
        GROUP BY match_id
        HAVING COUNT(*) > 24
        ORDER BY duplicates DESC
    )
);
ROLLBACK;
COMMIT;

SELECT match_id FROM (
        SELECT DISTINCT match_id, COUNT(*) AS duplicates
        FROM match_pick_bans
        GROUP BY match_id
        HAVING COUNT(*) > 24
        ORDER BY duplicates DESC
    );
SELECT DISTINCT mpb.order FROM match_pick_bans mpb ORDER BY mpb.order;