#!/usr/bin/env python3
"""Recompute stress ledger digest per ingest_contract (SHA-256)."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


def digest_for(path: Path) -> str:
    raw = path.read_text()
    patched = re.sub(
        r'"ledger_digest": "[0-9a-f]{64}"',
        '"ledger_digest": ""',
        raw,
        count=1,
    )
    return hashlib.sha256(patched.encode()).hexdigest()


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "/app/output/stress_ledger.json")
    ledger = json.loads(target.read_text())
    print(digest_for(target))
    print(ledger["summary"].get("ledger_digest", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
