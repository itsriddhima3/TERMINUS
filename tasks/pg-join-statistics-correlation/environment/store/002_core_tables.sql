CREATE TABLE dim_region (
  region_id integer PRIMARY KEY,
  region_code text NOT NULL UNIQUE,
  tier text NOT NULL
);

CREATE TABLE dim_facility (
  facility_id integer PRIMARY KEY,
  region_id integer NOT NULL REFERENCES dim_region(region_id),
  facility_code text NOT NULL UNIQUE,
  capacity_units integer NOT NULL
);

CREATE TABLE dim_zone (
  zone_id integer PRIMARY KEY,
  region_id integer NOT NULL REFERENCES dim_region(region_id),
  zone_code text NOT NULL,
  climate text NOT NULL
);

CREATE TABLE dim_lane (
  lane_id integer PRIMARY KEY,
  region_id integer NOT NULL REFERENCES dim_region(region_id),
  lane_code text NOT NULL UNIQUE,
  mode text NOT NULL
);

CREATE TABLE dim_carrier (
  carrier_id integer PRIMARY KEY,
  carrier_code text NOT NULL UNIQUE,
  service_tier text NOT NULL
);

CREATE TABLE dim_sku (
  sku_id integer PRIMARY KEY,
  sku_code text NOT NULL UNIQUE,
  weight_kg numeric(8, 2) NOT NULL
);

CREATE TABLE dim_supplier (
  supplier_id integer PRIMARY KEY,
  supplier_code text NOT NULL UNIQUE,
  region_id integer NOT NULL REFERENCES dim_region(region_id)
);

CREATE TABLE bridge_facility_zone (
  facility_id integer PRIMARY KEY REFERENCES dim_facility(facility_id),
  region_id integer NOT NULL,
  zone_code text NOT NULL,
  priority_band integer NOT NULL
);

CREATE TABLE bridge_lane_carrier (
  lane_id integer NOT NULL REFERENCES dim_lane(lane_id),
  carrier_id integer NOT NULL REFERENCES dim_carrier(carrier_id),
  rank_order integer NOT NULL,
  PRIMARY KEY (lane_id, carrier_id)
);

CREATE TABLE fact_shipment (
  shipment_id integer PRIMARY KEY,
  facility_id integer NOT NULL REFERENCES dim_facility(facility_id),
  region_id integer NOT NULL,
  zone_code text NOT NULL,
  supplier_id integer NOT NULL REFERENCES dim_supplier(supplier_id),
  status_code text NOT NULL
);

CREATE TABLE fact_shipment_line (
  line_id integer PRIMARY KEY,
  shipment_id integer NOT NULL REFERENCES fact_shipment(shipment_id),
  sku_id integer NOT NULL REFERENCES dim_sku(sku_id),
  qty integer NOT NULL
);

CREATE TABLE fact_route_leg (
  leg_id integer PRIMARY KEY,
  shipment_id integer NOT NULL REFERENCES fact_shipment(shipment_id),
  lane_id integer NOT NULL REFERENCES dim_lane(lane_id),
  carrier_id integer NOT NULL REFERENCES dim_carrier(carrier_id),
  seq_no integer NOT NULL
);

CREATE TABLE fact_inventory_snapshot (
  snapshot_id integer PRIMARY KEY,
  facility_id integer NOT NULL REFERENCES dim_facility(facility_id),
  sku_id integer NOT NULL REFERENCES dim_sku(sku_id),
  region_id integer NOT NULL,
  zone_code text NOT NULL,
  on_hand integer NOT NULL
);

CREATE TABLE fact_handling_event (
  event_id integer PRIMARY KEY,
  shipment_id integer NOT NULL REFERENCES fact_shipment(shipment_id),
  facility_id integer NOT NULL REFERENCES dim_facility(facility_id),
  event_code text NOT NULL
);

CREATE TABLE fact_charge (
  charge_id integer PRIMARY KEY,
  shipment_id integer NOT NULL REFERENCES fact_shipment(shipment_id),
  carrier_id integer NOT NULL REFERENCES dim_carrier(carrier_id),
  amount_cents integer NOT NULL
);
