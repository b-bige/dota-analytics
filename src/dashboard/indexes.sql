-- Active: 1771411304973@@165.22.73.33@5432@dota@public
CREATE INDEX idx_start_date_time ON match_details ("startDateTimeHuman");
CREATE INDEX idx_did_radiant_win ON match_details ("didRadiantWin");
CREATE INDEX idx_match_players_heroid ON match_players("heroId");
CREATE INDEX idx_match_players_matchid ON match_players(match_id);
CREATE INDEX idx_match_pick_bans_heroid ON match_pick_bans("heroId");

CREATE INDEX idx_mpb_matchid_ispick ON match_pick_bans(match_id, "isPick", "heroId");
CREATE INDEX idx_display_name ON league_details ("displayName");

CREATE INDEX idx_match_id ON match_players ("match_id");
CREATE INDEX idx_hero_id ON match_players ("heroId");