-- Superseded scope accessor experiment. Do not apply alongside /app/q/x7q.sql.

CREATE OR REPLACE FUNCTION w2_legacy_scope()
RETURNS integer
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT current_setting('app.scope_id', true)::integer
$$;
