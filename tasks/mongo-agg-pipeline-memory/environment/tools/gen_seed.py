#!/usr/bin/env python3
"""Generate deterministic events seed NDJSON for telemetry_db."""

from __future__ import annotations

import json
from pathlib import Path

REGIONS = ("EMEA", "APAC", "AMER")
EVENTS = ("purchase", "click", "view")
DOC_COUNT = 120_000
OUT = Path("/app/data/events_seed.ndjson")


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    emea_purchase_total = 0
    emea_purchase_count = 0
    with OUT.open("w", encoding="utf-8") as handle:
        for i in range(DOC_COUNT):
            region = REGIONS[i % 3]
            event_type = EVENTS[(i // 3) % 3]
            value = (i % 100) + 1
            doc = {
                "shard_id": i % 64,
                "region": region,
                "event_type": event_type,
                "value": value,
                "seq": i,
            }
            handle.write(json.dumps(doc, separators=(",", ":")) + "\n")
            if region == "EMEA" and event_type == "purchase":
                emea_purchase_total += value
                emea_purchase_count += 1
    meta = {
        "doc_count": DOC_COUNT,
        "emea_purchase_count": emea_purchase_count,
        "emea_purchase_total": emea_purchase_total,
    }
    Path("/app/data/seed_meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
