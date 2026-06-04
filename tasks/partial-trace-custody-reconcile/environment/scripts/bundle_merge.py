#!/usr/bin/env python3
"""Merge per-pack JSON fragments into custody_bundle.json."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

APP = Path("/app")
OUT = APP / "output" / "custody_bundle.json"
REGISTRY = APP / "config" / "scenarios.json"


def main() -> None:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    packs: list[dict] = []
    failed: list[str] = []
    for pack_id in reg["scenario_ids"]:
        frag = APP / "output" / f".pack_{pack_id}.json"
        data = json.loads(frag.read_text(encoding="utf-8"))
        packs.append(data)
        if not data.get("pack_ok", False):
            failed.append(pack_id)
    failed.sort()
    packs.sort(key=lambda p: p["pack_id"])
    run_id = hashlib.sha256(
        json.dumps(packs, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    doc = {
        "run_id": run_id,
        "packs": packs,
        "aggregate": {
            "failed_packs": len(failed),
            "failed_pack_ids": failed,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
