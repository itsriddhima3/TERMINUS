-- Lane/carrier cardinality tracking (orthogonal to region/zone spine predicates).

CREATE STATISTICS IF NOT EXISTS st_w9_lane (dependencies) ON lane_id, carrier_id FROM bridge_lane_carrier;

ANALYZE bridge_lane_carrier;
