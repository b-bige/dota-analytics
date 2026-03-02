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

--TODO Separate tables more

