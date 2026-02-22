-- Active: 1771411304973@@165.22.73.33@5432@dota
ALTER TABLE match_outpost_updates
    ADD CONSTRAINT fk_match_outpost_updates_snapshot_id
    FOREIGN KEY (snapshot_id)
    REFERENCES match_snapshots (snapshot_id);

