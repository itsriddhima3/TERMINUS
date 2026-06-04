#!/bin/bash
set -euo pipefail

/app/init/ensure_pg.sh

apply_sql() {
  local sql_file="$1"
  local tries=5
  while (( tries > 0 )); do
    if psql -U postgres -d saas_db -v ON_ERROR_STOP=1 -f "$sql_file"; then
      return 0
    fi
    sleep 0.5
    tries=$((tries - 1))
  done
  return 1
}

cat > /app/q/x7q.sql <<'SQL'
CREATE OR REPLACE FUNCTION fn_k7()
RETURNS integer
LANGUAGE sql
VOLATILE
AS $$
  SELECT current_setting('app.scope_id', true)::integer
$$;

CREATE OR REPLACE FUNCTION fn_k7_guard()
RETURNS boolean
LANGUAGE sql
VOLATILE
AS $$
  SELECT fn_k7() IS NOT NULL AND fn_k7() > 0
$$;

CREATE OR REPLACE FUNCTION fn_k7_refresh()
RETURNS void
LANGUAGE plpgsql
VOLATILE
AS $$
BEGIN
  PERFORM set_config('app.scope_id', current_setting('app.scope_id', true), false);
END;
$$;

COMMENT ON FUNCTION fn_k7() IS 'Session scope accessor used by reporting paths.';
COMMENT ON FUNCTION fn_k7_guard() IS 'Validates that the active scope handle is present before reads.';
COMMENT ON FUNCTION fn_k7_refresh() IS 'Rebinds the scope handle for long-lived sessions.';
SQL

cat > /app/q/m2p.sql <<'SQL'
DROP POLICY IF EXISTS pol_ledger_read ON ledger;
CREATE POLICY pol_ledger_read ON ledger
  FOR SELECT
  USING (
    fn_k7_guard()
    AND org_ref = fn_k7()
    AND active IS NOT NULL
  );

DROP POLICY IF EXISTS pol_contacts_read ON contacts;
CREATE POLICY pol_contacts_read ON contacts
  FOR SELECT
  USING (
    fn_k7_guard()
    AND org_ref = fn_k7()
    AND char_length(name) > 0
  );

DROP POLICY IF EXISTS pol_inventory_read ON inventory;
CREATE POLICY pol_inventory_read ON inventory
  FOR SELECT
  USING (
    fn_k7_guard()
    AND org_ref = fn_k7()
    AND qty >= 0
  );

DROP POLICY IF EXISTS pol_audit_read ON audit_log;
CREATE POLICY pol_audit_read ON audit_log
  FOR SELECT
  USING (
    fn_k7_guard()
    AND org_ref = fn_k7()
    AND event_code IS NOT NULL
  );
SQL

cat > /app/v/h3v.sql <<'SQL'
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'svc_runner') THEN
    CREATE ROLE svc_runner LOGIN PASSWORD 'runner_pass';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'svc_reader') THEN
    CREATE ROLE svc_reader LOGIN PASSWORD 'reader_pass';
  END IF;
END$$;

ALTER ROLE svc_runner SET search_path = public;
ALTER ROLE svc_reader SET search_path = public;
ALTER ROLE svc_runner SET plan_cache_mode = force_custom_plan;
ALTER ROLE svc_runner SET statement_timeout = '60s';
ALTER ROLE svc_reader SET default_transaction_read_only = on;
ALTER ROLE svc_reader SET statement_timeout = '30s';
SQL

cat > /app/q/n4w.sql <<'SQL'
CREATE OR REPLACE FUNCTION n4w_touch()
RETURNS trigger
LANGUAGE plpgsql
VOLATILE
AS $$
BEGIN
  PERFORM fn_k7_refresh();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS n4w_touch_trg ON org_dim;
CREATE TRIGGER n4w_touch_trg
  AFTER UPDATE ON org_dim
  FOR EACH ROW
  EXECUTE FUNCTION n4w_touch();
SQL

for sql_file in \
  /app/q/x7q.sql \
  /app/q/m2p.sql \
  /app/q/n4w.sql \
  /app/v/h3v.sql
do
  apply_sql "$sql_file"
done

/app/init/post_boot.sh

mkdir -p /app/output
bash /app/app/audit_runner.sh

python3 - <<'PY'
import json
from pathlib import Path

report = json.loads(Path("/app/output/boundary_audit.json").read_text(encoding="utf-8"))
for name, row in report["scenarios"].items():
    if row["cross_scope_visible"] or row["foreign_labels_seen"]:
        raise SystemExit(f"oracle leak remains in scenario {name}")
PY
