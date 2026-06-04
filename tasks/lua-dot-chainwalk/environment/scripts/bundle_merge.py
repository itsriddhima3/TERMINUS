#!/usr/bin/env python3
"""Assemble verdict_bundle.json from per-pack fragment files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def merge(registry_path: Path, output_dir: Path, bundle_path: Path) -> None:
    reg = json.loads(registry_path.read_text(encoding="utf-8"))
    packs = []
    failed: list[str] = []
    for pack_id in reg["pack_ids"]:
        frag = output_dir / f".pack_{pack_id}.json"
        data = json.loads(frag.read_text(encoding="utf-8"))
        packs.append(data)
        if data.get("pack_rc", 0) != 0:
            failed.append(pack_id)
    failed.sort()
    run_id = hashlib.sha256(
        json.dumps(packs, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]
    doc = {
        "run_id": run_id,
        "packs": packs,
        "aggregate": {
            "failed_packs": len(failed),
            "failed_pack_ids": failed,
        },
    }
    bundle_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    merge(
        Path("/app/config/case_registry.json"),
        Path("/app/output"),
        Path("/app/output/verdict_bundle.json"),
    )
