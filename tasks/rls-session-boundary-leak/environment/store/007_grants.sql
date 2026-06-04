REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO svc_runner, svc_reader;

GRANT SELECT ON org_dim TO svc_runner, svc_reader;
GRANT SELECT ON ledger TO svc_runner, svc_reader;
GRANT SELECT ON contacts TO svc_runner, svc_reader;
GRANT SELECT ON inventory TO svc_runner, svc_reader;
GRANT SELECT ON audit_log TO svc_runner, svc_reader;
