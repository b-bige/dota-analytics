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