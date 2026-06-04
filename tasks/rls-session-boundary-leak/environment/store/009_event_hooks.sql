CREATE OR REPLACE FUNCTION noop_scope_log()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS noop_scope_log_trg ON org_dim;
CREATE TRIGGER noop_scope_log_trg
  AFTER INSERT ON org_dim
  FOR EACH ROW
  EXECUTE FUNCTION noop_scope_log();
