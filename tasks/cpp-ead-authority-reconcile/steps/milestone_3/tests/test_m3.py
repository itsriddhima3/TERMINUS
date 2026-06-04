"""Milestone 3 — compliance report and unresolved queue."""

import json
import subprocess
import time
import urllib.request
from pathlib import Path

COMPLIANCE = Path("/app/output/compliance.json")
UNRESOLVED = Path("/app/output/unresolved.jsonl")
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


def _run_report() -> None:
    _ensure_api()
    subprocess.run(["/app/bin/arcctl", "parse", BATCH], check=True, capture_output=True)
    subprocess.run(["/app/bin/arcctl", "link", BATCH], check=True, capture_output=True)
    subprocess.run(["/app/bin/arcctl", "report", BATCH], check=True, capture_output=True)


class TestMilestone3:
    def test_m3_compliance_batch_id(self) -> None:
        """compliance.json names ARC-2024-Q2."""
        _run_report()
        doc = json.loads(COMPLIANCE.read_text(encoding="utf-8"))
        assert doc["batch_id"] == BATCH

    def test_m3_summary_total_three(self) -> None:
        """Summary counts three collections."""
        _run_report()
        doc = json.loads(COMPLIANCE.read_text(encoding="utf-8"))
        assert doc["summary"]["total"] == 3

    def test_m3_summary_fully_linked_three(self) -> None:
        """All three collections fully linked after repair."""
        _run_report()
        doc = json.loads(COMPLIANCE.read_text(encoding="utf-8"))
        assert doc["summary"]["fully_linked"] == 3

    def test_m3_summary_unresolved_zero(self) -> None:
        """No unresolved entities remain in the batch."""
        _run_report()
        doc = json.loads(COMPLIANCE.read_text(encoding="utf-8"))
        assert doc["summary"]["unresolved_count"] == 0

    def test_m3_accession_pass_three(self) -> None:
        """All accession checks pass."""
        _run_report()
        doc = json.loads(COMPLIANCE.read_text(encoding="utf-8"))
        assert doc["summary"]["accession_pass"] == 3
        assert doc["summary"]["accession_fail"] == 0

    def test_m3_compliance_records_count(self) -> None:
        """Compliance bundle retains all three linked records."""
        _run_report()
        doc = json.loads(COMPLIANCE.read_text(encoding="utf-8"))
        assert len(doc["records"]) == 3

    def test_m3_unresolved_jsonl_empty(self) -> None:
        """Unresolved queue is empty when every entity linked."""
        _run_report()
        lines = [ln for ln in UNRESOLVED.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert lines == []

    def test_m3_ms_accession_in_compliance(self) -> None:
        """MS-0456 accession remains valid in compliance records."""
        _run_report()
        doc = json.loads(COMPLIANCE.read_text(encoding="utf-8"))
        ms = next(r for r in doc["records"] if r["collection_id"] == "MS-0456")
        assert ms["accession_candidate"] == "MS-0456"
        assert ms["accession_valid"] is True

    def test_m3_ua_accession_dot_form(self) -> None:
        """UA.12.003 keeps dot accession form."""
        _run_report()
        doc = json.loads(COMPLIANCE.read_text(encoding="utf-8"))
        ua = next(r for r in doc["records"] if r["collection_id"] == "UA.12.003")
        assert ua["accession_candidate"] == "UA.12.003"
        assert ua["accession_valid"] is True

    def test_m3_ua_creator_in_compliance(self) -> None:
        """UA.12.003 corporate creator present in compliance bundle."""
        _run_report()
        doc = json.loads(COMPLIANCE.read_text(encoding="utf-8"))
        ua = next(r for r in doc["records"] if r["collection_id"] == "UA.12.003")
        assert ua["creator_primary"] == "auth-corp-001"

    def test_m3_compliance_records_mirror_linked_auth_ids(self) -> None:
        """Compliance bundle mirrors linked authority ids and accession state."""
        _run_report()
        linked = json.loads(Path("/app/output/linked.json").read_text(encoding="utf-8"))
        compliance = json.loads(COMPLIANCE.read_text(encoding="utf-8"))
        linked_by_id = {r["collection_id"]: r for r in linked["records"]}
        compliance_by_id = {r["collection_id"]: r for r in compliance["records"]}
        assert set(compliance_by_id) == set(linked_by_id)
        mirror_fields = (
            "creator_primary",
            "subject_headings",
            "place_names",
            "accession_candidate",
            "accession_valid",
            "geo_heading_count",
        )
        for cid, linked_row in linked_by_id.items():
            comp_row = compliance_by_id[cid]
            for field in mirror_fields:
                assert comp_row[field] == linked_row[field], f"{cid}.{field}"
        summary = compliance["summary"]
        assert summary["total"] == len(linked["records"])
        assert summary["fully_linked"] == summary["total"]
        assert summary["unresolved_count"] == 0
        assert len(compliance["records"]) == summary["total"]

    def test_m3_ms_optional_geographic_still_fully_linked(self) -> None:
        """MS-0456 has no geogname yet remains fully linked per handbook 23.5."""
        _run_report()
        linked = json.loads(Path("/app/output/linked.json").read_text(encoding="utf-8"))
        compliance = json.loads(COMPLIANCE.read_text(encoding="utf-8"))
        ms = next(r for r in linked["records"] if r["collection_id"] == "MS-0456")
        assert ms["geo_heading_count"] == 0
        assert ms["place_names"] == ""
        assert ms["creator_primary"] == "auth-per-042"
        assert ms["subject_headings"] == "subj-200"
        assert ms["accession_valid"] is True
        assert compliance["summary"]["fully_linked"] == 3
