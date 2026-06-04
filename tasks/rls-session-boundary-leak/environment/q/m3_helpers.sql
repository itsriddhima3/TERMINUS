CREATE OR REPLACE FUNCTION op_m3(p_org integer, p_code text)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM audit_log
    WHERE org_ref = p_org AND event_code = p_code
  )
$$;

CREATE OR REPLACE FUNCTION op_m3_for_session(p_code text)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
  SELECT op_m3(current_setting('app.scope_id', true)::integer, p_code)
$$;
