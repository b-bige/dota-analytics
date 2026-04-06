-- Active: 1771411304973@@165.22.73.33@5432@dota@public
ALTER TABLE match_details 
ADD COLUMN "startDateTimeHuman" TIMESTAMP;

ALTER TABLE match_details 
ADD COLUMN "endDateTimeHuman" TIMESTAMP;

BEGIN;
UPDATE match_details SET "startDateTimeHuman" = TO_TIMESTAMP("startDateTime");
UPDATE match_details SET "endDateTimeHuman" = TO_TIMESTAMP("endDateTime");
ROLLBACK;

ALTER TABLE match_details
ADD COLUMN avg_radiant_rating DOUBLE PRECISION,
ADD COLUMN avg_dire_rating DOUBLE PRECISION;

ALTER TABLE match_details
ADD COLUMN predicted_radiant_win BOOLEAN;

CREATE TABLE IF NOT EXISTS live_matches (
    match_id BIGINT PRIMARY KEY,
    league_id INTEGER,
    league_name TEXT,
    start_date_time TIMESTAMP,
    radiant_id BIGINT,
    dire_id BIGINT,
    radiant_name TEXT,
    dire_name TEXT,
    radiant_logo TEXT,
    dire_logo TEXT,
    radiant_score INTEGER DEFAULT 0,
    dire_score INTEGER DEFAULT 0,
    game_time INTEGER, -- Seconds since start
    radiant_lead INTEGER, -- Positive for Radiant, Negative for Dire
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE match_players
ADD COLUMN kills SMALLINT,
ADD COLUMN deaths SMALLINT,
ADD COLUMN assists SMALLINT;
CREATE TABLE team_logos (
    team_id BIGINT,
    logo_url TEXT
);

ALTER TABLE match_details
ADD COLUMN radiant_score SMALLINT,
ADD COLUMN dire_score SMALLINT;

ALTER TABLE match_wards ALTER COLUMN "positionX" TYPE NUMERIC;
ALTER TABLE match_wards ALTER COLUMN "positionY" TYPE NUMERIC;

CREATE TABLE wards_backup AS SELECT * FROM match_wards;