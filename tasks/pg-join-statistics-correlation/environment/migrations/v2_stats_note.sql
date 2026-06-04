-- Historical note: stats refresh cadence tracked here for ops dashboards.

CREATE TABLE IF NOT EXISTS stats_refresh_log (
  entry_id serial PRIMARY KEY,
  captured_at timestamptz NOT NULL DEFAULT now(),
  note text NOT NULL
);

INSERT INTO stats_refresh_log(note)
VALUES ('seed complete');
