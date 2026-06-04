CREATE OR REPLACE FUNCTION audit_scalar(p_label TEXT)
RETURNS BIGINT
LANGUAGE sql
STABLE
AS $$
  SELECT COALESCE((SELECT rollup_qty FROM partition_dim WHERE label = p_label), 0);
$$;
