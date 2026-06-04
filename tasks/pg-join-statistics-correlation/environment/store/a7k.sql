-- Statistics target defaults for bridge and fact columns (planner ops bundle).

ALTER TABLE bridge_facility_zone ALTER COLUMN region_id SET STATISTICS 100;
ALTER TABLE bridge_facility_zone ALTER COLUMN zone_code SET STATISTICS 100;
ALTER TABLE fact_shipment ALTER COLUMN region_id SET STATISTICS 100;
ALTER TABLE fact_shipment ALTER COLUMN zone_code SET STATISTICS 100;
ALTER TABLE fact_inventory_snapshot ALTER COLUMN region_id SET STATISTICS 100;
ALTER TABLE fact_inventory_snapshot ALTER COLUMN zone_code SET STATISTICS 100;
