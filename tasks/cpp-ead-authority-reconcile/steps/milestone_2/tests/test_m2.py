"""Milestone 2 — authority API linking."""

import json
import subprocess
import time
import urllib.request
from pathlib import Path

LINKED = Path("/app/output/linked.json")
BATCH = "ARC-2024-Q2"
API = "http://127.0.0.1:3000"


def _ensure_api() -> None:
    try:
        urllib.request.urlopen(f"{API}/health", timeout=1).read()
        return
    except Exception:
        pass
    subprocess.run(["/app/scripts/start-api.sh"], check=False, capture_output=True)
    deadline = time.time() + 8.0
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{API}/health", timeout=1).read()
            return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("authority API did not become ready")


def _run_link() -> None:
    _ensure_api()
    subprocess.run(["/app/bin/arcctl", "parse", BATCH], check=True, capture_output=True)
    subprocess.run(["/app/bin/arcctl", "link", BATCH], check=True, capture_output=True)


def _records() -> list[dict]:
    _run_link()
    doc = json.loads(LINKED.read_text(encoding="utf-8"))
    return doc["records"]


class TestMilestone2:
    def test_m2_linked_batch_id(self) -> None:
        """linked.json names ARC-2024-Q2 batch."""
        _run_link()
        doc = json.loads(LINKED.read_text(encoding="utf-8"))
        assert doc["batch_id"] == BATCH

    def test_m2_ua_corporate_creator_wins(self) -> None:
        """UA-0012 links to University Archives corporate authority."""
        recs = _records()
        ua = next(r for r in recs if r["collection_id"] == "UA.12.003")
        assert ua["creator_primary"] == "auth-corp-001"

    def test_m2_ua_subject_stem(self) -> None:
        """UA-0012 subject resolves via College buildings stem."""
        recs = _records()
        ua = next(r for r in recs if r["collection_id"] == "UA.12.003")
        assert ua["subject_headings"] == "subj-100"

    def test_m2_ua_approx_place_tier2(self) -> None:
        """UA-0012 approximate Washtenaw County uses tier-two place id."""
        recs = _records()
        ua = next(r for r in recs if r["collection_id"] == "UA.12.003")
        assert ua["place_names"] == "place-302"

    def test_m2_ms_creator(self) -> None:
        """MS-0456 links Wilson, Edith personal authority."""
        recs = _records()
        ms = next(r for r in recs if r["collection_id"] == "MS-0456")
        assert ms["creator_primary"] == "auth-per-042"

    def test_m2_ms_subject_stem(self) -> None:
        """MS-0456 Women authors stem resolves."""
        recs = _records()
        ms = next(r for r in recs if r["collection_id"] == "MS-0456")
        assert ms["subject_headings"] == "subj-200"

    def test_m2_ms_accession_ms_prefix(self) -> None:
        """MS-0456 accession candidate keeps MS- prefix."""
        recs = _records()
        ms = next(r for r in recs if r["collection_id"] == "MS-0456")
        assert ms["accession_candidate"] == "MS-0456"
        assert ms["accession_valid"] is True

    def test_m2_ph_creator(self) -> None:
        """PH.0789 links Bentley Historical Library corporate authority."""
        recs = _records()
        ph = next(r for r in recs if r["collection_id"] == "PH.0789")
        assert ph["creator_primary"] == "auth-corp-007"

    def test_m2_ph_place_ann_arbor(self) -> None:
        """PH.0789 Ann Arbor resolves after parenthetical strip."""
        recs = _records()
        ph = next(r for r in recs if r["collection_id"] == "PH.0789")
        assert ph["place_names"] == "place-301"

    def test_m2_three_linked_records(self) -> None:
        """All three collections present in linked output."""
        recs = _records()
        ids = {r["collection_id"] for r in recs}
        assert ids == {"UA.12.003", "MS-0456", "PH.0789"}

    def test_m2_ua_corporate_precedence_over_resolvable_personal(self) -> None:
        """UA-0012 rejects resolvable personal John Smith in favor of corporate body."""
        recs = _records()
        ua = next(r for r in recs if r["collection_id"] == "UA.12.003")
        assert ua["creator_primary"] == "auth-corp-001"
        assert ua["creator_primary"] != "auth-per-999"

    def test_m2_batch_accession_and_subjects_reconcile(self) -> None:
        """Subject stems and accession ids reconcile for every linked collection."""
        recs = _records()
        by_id = {r["collection_id"]: r for r in recs}
        assert by_id["UA.12.003"]["subject_headings"] == "subj-100"
        assert by_id["MS-0456"]["subject_headings"] == "subj-200"
        for cid in ("UA.12.003", "MS-0456", "PH.0789"):
            rec = by_id[cid]
            assert rec["accession_candidate"] == cid
            assert rec["accession_valid"] is True

    def test_m2_place_api_honors_tier_two_query(self) -> None:
        """Place authority service resolves approximate county at tier two."""
        _ensure_api()
        import urllib.parse

        q = urllib.parse.urlencode({"name": "Washtenaw County", "tier": "2"})
        with urllib.request.urlopen(f"{API}/api/v1/places/resolve?{q}", timeout=2) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        assert body["place_id"] == "place-302"
        assert body["tier"] == 2
