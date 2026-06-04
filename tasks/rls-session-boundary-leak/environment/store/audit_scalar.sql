CREATE OR REPLACE FUNCTION cfg_p9()
RETURNS numeric
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT 0::numeric
$$;

CREATE OR REPLACE FUNCTION audit_scalar_total(p_org integer)
RETURNS numeric
LANGUAGE sql
STABLE
AS $$
  SELECT coalesce(sum(amount), 0)
  FROM ledger
  WHERE org_ref = p_org AND active
$$;
