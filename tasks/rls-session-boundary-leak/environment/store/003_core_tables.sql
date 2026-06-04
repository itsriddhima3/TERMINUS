CREATE TABLE IF NOT EXISTS org_dim (
  org_ref integer PRIMARY KEY,
  label text NOT NULL UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ledger (
  id serial PRIMARY KEY,
  org_ref integer NOT NULL REFERENCES org_dim(org_ref),
  label text NOT NULL,
  amount numeric(12, 2) NOT NULL,
  active boolean NOT NULL DEFAULT true,
  status ledger_status NOT NULL DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS contacts (
  id serial PRIMARY KEY,
  org_ref integer NOT NULL REFERENCES org_dim(org_ref),
  name text NOT NULL,
  email text NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory (
  id serial PRIMARY KEY,
  org_ref integer NOT NULL REFERENCES org_dim(org_ref),
  sku text NOT NULL,
  qty integer NOT NULL CHECK (qty >= 0)
);

CREATE TABLE IF NOT EXISTS audit_log (
  id bigserial PRIMARY KEY,
  org_ref integer NOT NULL,
  event_code text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  recorded_at timestamptz NOT NULL DEFAULT now()
);
