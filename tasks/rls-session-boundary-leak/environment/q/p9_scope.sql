-- Reporting helper; not referenced by row filters.
CREATE OR REPLACE FUNCTION p9_scope_echo()
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT current_setting('app.scope_id', true)
$$;
