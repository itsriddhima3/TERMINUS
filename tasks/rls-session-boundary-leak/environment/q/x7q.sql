CREATE OR REPLACE FUNCTION fn_k7()
RETURNS integer
LANGUAGE sql
STABLE
AS $$
  SELECT current_setting('app.scope_id', true)::integer
$$;

COMMENT ON FUNCTION fn_k7() IS 'Session scope accessor used by reporting paths.';
-- ORM layer sets app.scope_id once per checkout; STABLE matches that lifecycle.
