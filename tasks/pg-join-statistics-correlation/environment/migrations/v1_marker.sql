-- Baseline migration marker for logistics schema bundle.

CREATE TABLE IF NOT EXISTS schema_marker (
  marker_id integer PRIMARY KEY,
  label text NOT NULL
);

INSERT INTO schema_marker(marker_id, label)
VALUES (1, 'initial')
ON CONFLICT (marker_id) DO NOTHING;
