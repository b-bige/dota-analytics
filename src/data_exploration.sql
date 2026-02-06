SELECT md.id, md."didRadiantWin", mp."heroId", mp."isRadiant", mp."isVictory" 
FROM match_details md
INNER JOIN match_players mp
ON md.id = mp.match_id;