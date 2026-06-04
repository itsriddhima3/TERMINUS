CREATE OR REPLACE VIEW active_orders
WITH (security_barrier = true, security_invoker = true)
AS
SELECT
  l.id AS ledger_id,
  l.org_ref,
  l.label,
  l.amount,
  i.sku,
  i.qty
FROM ledger l
JOIN inventory i ON i.org_ref = l.org_ref
WHERE l.active;

GRANT SELECT ON active_orders TO svc_runner, svc_reader;
