#!/usr/bin/env python3
"""Generate correlated seed data for the fulfillment schema."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "store" / "900_seed_data.sql"

REGIONS = 10
FACILITIES_PER_REGION = 40
SKUS = 500
SHIPMENTS = 8000


def q(value: str) -> str:
    return value.replace("'", "''")


def main() -> None:
    lines: list[str] = ["BEGIN;", "TRUNCATE bridge_facility_zone, fact_charge, fact_handling_event,",
                        " fact_inventory_snapshot, fact_route_leg, fact_shipment_line, fact_shipment,",
                        " dim_supplier, dim_sku, dim_carrier, dim_lane, bridge_lane_carrier,",
                        " dim_zone, dim_facility, dim_region RESTART IDENTITY CASCADE;"]

    for rid in range(1, REGIONS + 1):
        code = f"RG-{rid:02d}"
        lines.append(
            f"INSERT INTO dim_region(region_id, region_code, tier) VALUES ({rid}, '{code}', 'T{(rid % 3) + 1}');"
        )

    fid = 1
    zid = 1
    for rid in range(1, REGIONS + 1):
        zone_code = f"Z-East-{rid}"
        lines.append(
            f"INSERT INTO dim_zone(zone_id, region_id, zone_code, climate) "
            f"VALUES ({zid}, {rid}, '{zone_code}', 'temperate');"
        )
        zid += 1
        for slot in range(FACILITIES_PER_REGION):
            lines.append(
                f"INSERT INTO dim_facility(facility_id, region_id, facility_code, capacity_units) "
                f"VALUES ({fid}, {rid}, 'FC-{rid:02d}-{slot:03d}', {100 + slot});"
            )
            lines.append(
                f"INSERT INTO bridge_facility_zone(facility_id, region_id, zone_code, priority_band) "
                f"VALUES ({fid}, {rid}, '{zone_code}', {(slot % 5) + 1});"
            )
            fid += 1

    for lid in range(1, 21):
        lines.append(
            f"INSERT INTO dim_lane(lane_id, region_id, lane_code, mode) "
            f"VALUES ({lid}, {((lid - 1) % REGIONS) + 1}, 'LN-{lid:02d}', 'road');"
        )

    for cid in range(1, 11):
        lines.append(
            f"INSERT INTO dim_carrier(carrier_id, carrier_code, service_tier) "
            f"VALUES ({cid}, 'CR-{cid:02d}', 'standard');"
        )

    for lid in range(1, 21):
        for cid in range(1, 4):
            lines.append(
                f"INSERT INTO bridge_lane_carrier(lane_id, carrier_id, rank_order) "
                f"VALUES ({lid}, {cid}, {cid});"
            )

    for sid in range(1, SKUS + 1):
        lines.append(
            f"INSERT INTO dim_sku(sku_id, sku_code, weight_kg) "
            f"VALUES ({sid}, 'SKU-{sid:05d}', {(sid % 50) + 1}.0);"
        )

    for spid in range(1, 31):
        lines.append(
            f"INSERT INTO dim_supplier(supplier_id, supplier_code, region_id) "
            f"VALUES ({spid}, 'SP-{spid:03d}', {(spid % REGIONS) + 1});"
        )

    for sh in range(1, SHIPMENTS + 1):
        rid = (sh % REGIONS) + 1
        fac = ((sh * 7) % (REGIONS * FACILITIES_PER_REGION)) + 1
        zone_code = f"Z-East-{rid}"
        lines.append(
            f"INSERT INTO fact_shipment(shipment_id, facility_id, region_id, zone_code, supplier_id, status_code) "
            f"VALUES ({sh}, {fac}, {rid}, '{zone_code}', {(sh % 30) + 1}, 'open');"
        )
        lines.append(
            f"INSERT INTO fact_shipment_line(line_id, shipment_id, sku_id, qty) "
            f"VALUES ({sh}, {sh}, {(sh % SKUS) + 1}, {(sh % 9) + 1});"
        )
        lines.append(
            f"INSERT INTO fact_route_leg(leg_id, shipment_id, lane_id, carrier_id, seq_no) "
            f"VALUES ({sh}, {sh}, {(sh % 20) + 1}, {(sh % 10) + 1}, 1);"
        )
        lines.append(
            f"INSERT INTO fact_inventory_snapshot(snapshot_id, facility_id, sku_id, region_id, zone_code, on_hand) "
            f"VALUES ({sh}, {fac}, {(sh % SKUS) + 1}, {rid}, '{zone_code}', {(sh % 120) + 1});"
        )
        lines.append(
            f"INSERT INTO fact_handling_event(event_id, shipment_id, facility_id, event_code) "
            f"VALUES ({sh}, {sh}, {fac}, 'scan');"
        )
        lines.append(
            f"INSERT INTO fact_charge(charge_id, shipment_id, carrier_id, amount_cents) "
            f"VALUES ({sh}, {sh}, {(sh % 10) + 1}, {(sh % 5000) + 100});"
        )

    lines.append("COMMIT;")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
