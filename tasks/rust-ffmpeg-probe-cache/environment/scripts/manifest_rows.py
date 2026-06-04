#!/usr/bin/env python3
"""List clip filenames per scenario from the stress manifest (TOML)."""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "/app/data/stress_manifest.toml")
    data = tomllib.loads(path.read_text())
    for lane in data.get("lanes", []):
        lane_id = lane.get("lane_id", "?")
        clips = lane.get("clips", [])
        print(f"{lane_id}:{' '.join(clips)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
