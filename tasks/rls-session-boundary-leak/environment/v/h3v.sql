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
-- plan_cache_mode left at cluster auto here; pool metrics review pending Q4.
