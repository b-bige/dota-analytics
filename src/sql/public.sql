-- Active: 1771411304973@@165.22.73.33@5432@dota@public
SELECT match_id, position, networth, "isRadiant", "isVictory" FROM match_players
WHERE networth IS NOT NULL AND position IS NOT NULL
GROUP BY match_id, position;