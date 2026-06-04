DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'svc_planner') THEN
    CREATE ROLE svc_planner LOGIN PASSWORD 'planner_pass';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'svc_reader') THEN
    CREATE ROLE svc_reader LOGIN PASSWORD 'reader_pass';
  END IF;
END$$;

GRANT CONNECT ON DATABASE logistics_db TO svc_planner, svc_reader;
GRANT USAGE ON SCHEMA public TO svc_planner, svc_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO svc_planner, svc_reader;
ALTER DEFAULT PRIVileges IN SCHEMA public GRANT SELECT ON TABLES TO svc_planner, svc_reader;

ALTER ROLE svc_planner SET search_path = public;
ALTER ROLE svc_reader SET search_path = public;
ALTER ROLE svc_planner SET work_mem = '64MB';
ALTER ROLE svc_planner SET enable_nestloop = on;
ALTER ROLE svc_planner SET enable_hashjoin = on;
