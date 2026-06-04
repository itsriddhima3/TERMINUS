-- Fifteen-table spine workload template; audit harness binds region and zone literals.
SELECT count(*)
FROM fact_shipment fs
JOIN dim_region dr ON dr.region_id = fs.region_id
JOIN dim_facility df ON df.facility_id = fs.facility_id
JOIN dim_zone dz ON dz.region_id = fs.region_id AND dz.zone_code = fs.zone_code
JOIN bridge_facility_zone bf ON bf.facility_id = fs.facility_id
  AND bf.region_id = fs.region_id
  AND bf.zone_code = fs.zone_code
JOIN fact_shipment_line fsl ON fsl.shipment_id = fs.shipment_id
JOIN dim_sku ds ON ds.sku_id = fsl.sku_id
JOIN fact_route_leg frl ON frl.shipment_id = fs.shipment_id
JOIN dim_lane dl ON dl.lane_id = frl.lane_id
JOIN dim_carrier dc ON dc.carrier_id = frl.carrier_id
JOIN bridge_lane_carrier blc ON blc.lane_id = frl.lane_id AND blc.carrier_id = frl.carrier_id
JOIN fact_inventory_snapshot fis ON fis.facility_id = fs.facility_id
  AND fis.sku_id = fsl.sku_id
  AND fis.region_id = fs.region_id
  AND fis.zone_code = fs.zone_code
JOIN fact_handling_event fhe ON fhe.shipment_id = fs.shipment_id
JOIN fact_charge fc ON fc.shipment_id = fs.shipment_id
JOIN dim_supplier dsp ON dsp.supplier_id = fs.supplier_id
WHERE bf.region_id = __REGION__
  AND bf.zone_code = '__ZONE__'
  AND fs.status_code = 'open';
