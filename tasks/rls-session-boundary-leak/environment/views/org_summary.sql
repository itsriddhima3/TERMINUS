CREATE OR REPLACE VIEW org_summary
AS
SELECT
  d.org_ref,
  d.label,
  audit_scalar_total(d.org_ref) AS active_total
FROM org_dim d;

GRANT SELECT ON org_summary TO svc_runner, svc_reader;
