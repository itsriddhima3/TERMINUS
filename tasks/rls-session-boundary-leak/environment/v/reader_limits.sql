-- pg_roles.rolconfig stores these as default_transaction_read_only=on and statement_timeout=30s
ALTER ROLE svc_reader SET default_transaction_read_only = on;
ALTER ROLE svc_reader SET statement_timeout = '30s';
