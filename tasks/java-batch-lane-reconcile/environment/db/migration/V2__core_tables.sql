CREATE TABLE partition_dim (
  label TEXT PRIMARY KEY,
  cap_slots INT NOT NULL,
  active_slots INT NOT NULL DEFAULT 0,
  rollup_qty BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE header_slice (
  id BIGSERIAL PRIMARY KEY,
  partition_label TEXT NOT NULL REFERENCES partition_dim(label),
  external_biz_id TEXT NOT NULL,
  stamp_version BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (partition_label, external_biz_id)
);

CREATE TABLE line_slice (
  id BIGSERIAL PRIMARY KEY,
  header_id BIGINT NOT NULL REFERENCES header_slice(id) ON DELETE CASCADE,
  sku TEXT NOT NULL,
  qty INT NOT NULL CHECK (qty > 0),
  stamp_version BIGINT NOT NULL DEFAULT 0
);

CREATE INDEX idx_line_header ON line_slice(header_id);

CREATE TABLE lane_attempt (
  id BIGSERIAL PRIMARY KEY,
  partition_label TEXT NOT NULL,
  external_biz_id TEXT NOT NULL,
  accepted_lines INT NOT NULL DEFAULT 0,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO partition_dim(label, cap_slots) VALUES
  ('North-Shelf', 6),
  ('East-Crate', 10),
  ('West-Bin', 4);
