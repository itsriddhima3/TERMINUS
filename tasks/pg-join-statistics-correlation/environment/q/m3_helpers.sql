CREATE OR REPLACE FUNCTION op_m3_for_session()
RETURNS integer
LANGUAGE sql
STABLE
AS $$
  SELECT COALESCE(current_setting('app.session_slot', true)::integer, 0)
$$;

CREATE OR REPLACE FUNCTION cfg_p9_lane_total(p_lane integer)
RETURNS bigint
LANGUAGE sql
STABLE
AS $$
  SELECT count(*) FROM bridge_lane_carrier blc WHERE blc.lane_id = p_lane
$$;

COMMENT ON FUNCTION op_m3_for_session IS 'Session slot reader for reporting harness.';
COMMENT ON FUNCTION cfg_p9_lane_total IS 'Lane carrier cardinality helper for dashboards.';
