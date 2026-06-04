-- nightly metrics snapshot (not on hot path)
CREATE TABLE IF NOT EXISTS metrics_n8f_snapshot (
  captured_at TIMESTAMPTZ PRIMARY KEY DEFAULT now(),
  payload JSONB NOT NULL
);
