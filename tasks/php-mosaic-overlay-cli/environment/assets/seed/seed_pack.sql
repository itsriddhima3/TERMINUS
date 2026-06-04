PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS packs (
    pack_id TEXT PRIMARY KEY,
    pack_label TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS challenges (
    challenge_id TEXT PRIMARY KEY,
    pack_id TEXT NOT NULL REFERENCES packs(pack_id),
    source_width INTEGER NOT NULL,
    source_height INTEGER NOT NULL,
    scene_a_path TEXT NOT NULL,
    scene_b_path TEXT NOT NULL,
    regions_path TEXT NOT NULL,
    base_units INTEGER NOT NULL DEFAULT 1000
);

CREATE TABLE IF NOT EXISTS region_defs (
    challenge_id TEXT NOT NULL REFERENCES challenges(challenge_id),
    region_id TEXT NOT NULL,
    region_label TEXT NOT NULL,
    polygon_json TEXT NOT NULL,
    PRIMARY KEY (challenge_id, region_id)
);

CREATE TABLE IF NOT EXISTS sessions (
    session_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    challenge_id TEXT NOT NULL REFERENCES challenges(challenge_id),
    opened_at_ms INTEGER NOT NULL,
    closed_at_ms INTEGER,
    closed_reason TEXT,
    score INTEGER,
    component_breakdown TEXT
);

CREATE TABLE IF NOT EXISTS marks (
    mark_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_row_id INTEGER NOT NULL REFERENCES sessions(session_row_id),
    sequence_no INTEGER NOT NULL,
    raised_at_ms INTEGER NOT NULL,
    input_col INTEGER NOT NULL,
    input_row INTEGER NOT NULL,
    matched_region_id TEXT,
    matched INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS hints (
    hint_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_row_id INTEGER NOT NULL REFERENCES sessions(session_row_id),
    sequence_no INTEGER NOT NULL,
    raised_at_ms INTEGER NOT NULL,
    incurred_penalty INTEGER NOT NULL DEFAULT 0,
    bucket_start_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at_ms INTEGER NOT NULL,
    action TEXT NOT NULL,
    detail TEXT
);

INSERT OR REPLACE INTO packs (pack_id, pack_label, created_at) VALUES
    ('starter_pack', 'Starter Mosaic Pack', 0);

INSERT OR REPLACE INTO challenges
    (challenge_id, pack_id, source_width, source_height, scene_a_path, scene_b_path, regions_path, base_units)
VALUES
    ('ch_alpha', 'starter_pack', 64, 32,
     'assets/challenges/ch_alpha/scene_a.png',
     'assets/challenges/ch_alpha/scene_b.png',
     'assets/challenges/ch_alpha/regions.json',
     1000),
    ('ch_bravo', 'starter_pack', 64, 32,
     'assets/challenges/ch_bravo/scene_a.png',
     'assets/challenges/ch_bravo/scene_b.png',
     'assets/challenges/ch_bravo/regions.json',
     1000);

INSERT OR REPLACE INTO region_defs (challenge_id, region_id, region_label, polygon_json) VALUES
    ('ch_alpha', 'alpha_region_top', 'upper_mid_block', '[[40,0],[50,0],[50,10],[40,10]]'),
    ('ch_alpha', 'alpha_region_left', 'lower_left_block', '[[0,22],[12,22],[12,30],[0,30]]'),
    ('ch_alpha', 'alpha_region_tri', 'center_triangle', '[[24,14],[40,14],[32,24]]'),
    ('ch_bravo', 'bravo_region_ne', 'upper_right_block', '[[54,0],[63,0],[63,8],[54,8]]'),
    ('ch_bravo', 'bravo_region_nw', 'upper_left_block', '[[0,0],[10,0],[10,8],[0,8]]'),
    ('ch_bravo', 'bravo_region_quad', 'center_quad', '[[28,18],[44,16],[44,28],[28,26]]');
