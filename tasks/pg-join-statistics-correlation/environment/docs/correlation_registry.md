# Spine predicate groups for the fifteen-table fulfillment workload.
#
# Each group names a table and the column pair whose joint selectivity affects
# replanning. Groups marked for spine participation must be catalogued before
# the audit harness will report acceptable estimate ratios.

## bridge_facility_zone
Columns: region_id and zone_code
Spine predicate: yes

## fact_shipment
Columns: region_id and zone_code
Spine predicate: yes

## fact_inventory_snapshot
Columns: region_id and zone_code
Spine predicate: yes

## dim_zone
Columns: region_id and zone_code
Spine predicate: yes

## bridge_lane_carrier
Columns: lane_id and carrier_id
Spine predicate: no
