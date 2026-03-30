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

CREATE TABLE team_logos (
    team_id BIGINT,
    logo_url TEXT
);

