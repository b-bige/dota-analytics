-- Active: 1771411304973@@165.22.73.33@5432@dota@public
CREATE INDEX idx_start_date_time ON match_details ("startDateTimeHuman");
CREATE INDEX idx_display_name ON league_details ("displayName");

CREATE INDEX idx_match_id ON match_players ("match_id");
CREATE INDEX idx_hero_id ON match_players ("heroId");