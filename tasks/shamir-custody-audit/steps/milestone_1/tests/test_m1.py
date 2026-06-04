"""Milestone 1 — Ceremony record loading and approval linkage."""

import json
import sqlite3
import subprocess
from pathlib import Path

BINARY = "/app/bin/audit"
DB = "/app/data/ceremonies.db"
DOSSIER = "/app/docs/ceremony-policy-v3.md"
REPORT = "/app/output/report.json"

EXPECTED_SESSIONS = {"sess-alpha", "sess-beta", "sess-gamma", "sess-delta"}
EXPECTED_SLOTS = {
    "sess-alpha": 5,
    "sess-beta": 4,
    "sess-gamma": 5,
    "sess-delta": 3,
}
EXPECTED_APPROVALS = {
    "sess-alpha": 3,
    "sess-beta": 2,
    "sess-gamma": 3,
    "sess-delta": 2,
}


def _run_audit() -> subprocess.CompletedProcess:
    return subprocess.run(
        [BINARY, "--db", DB, "--dossier", DOSSIER, "--out", REPORT],
        capture_output=True,
        text=True,
        timeout=60,
    )


def _load_report() -> dict:
    return json.loads(Path(REPORT).read_text())


def _by_session(report: dict) -> dict:
    return {e["session_id"]: e for e in report["audit_results"]}


class TestMilestone1:
    def test_m1_audit_exits_zero(self):
        """Audit tool runs without error and exits 0."""
        proc = _run_audit()
        assert proc.returncode == 0, f"stderr: {proc.stderr}"

    def test_m1_report_exists(self):
        """Report file is written to the expected output path."""
        _run_audit()
        assert Path(REPORT).exists(), f"Report not found at {REPORT}"

    def test_m1_report_schema(self):
        """Report root contains audit_results array."""
        _run_audit()
        report = _load_report()
        assert "audit_results" in report
        assert isinstance(report["audit_results"], list)
        assert len(report["audit_results"]) > 0

    def test_m1_all_sessions_present(self):
        """Report contains an entry for each of the four sessions."""
        _run_audit()
        report = _load_report()
        found = {e["session_id"] for e in report["audit_results"]}
        for sid in EXPECTED_SESSIONS:
            assert sid in found, f"Missing session {sid} in report"

    def test_m1_slots_loaded_correct(self):
        """slots_loaded matches total_slots in the sessions table."""
        _run_audit()
        by_sess = _by_session(_load_report())
        for sid, expected in EXPECTED_SLOTS.items():
            assert sid in by_sess, f"Session {sid} missing"
            got = by_sess[sid]["slots_loaded"]
            assert got == expected, f"{sid}: slots_loaded={got}, want {expected}"

    def test_m1_approvals_linked_nonzero(self):
        """Sessions with approvals in the database report approvals_linked > 0."""
        _run_audit()
        by_sess = _by_session(_load_report())
        for sid in ("sess-alpha", "sess-beta", "sess-gamma", "sess-delta"):
            linked = by_sess[sid]["approvals_linked"]
            assert linked > 0, (
                f"{sid}: approvals_linked={linked}, expected > 0 — "
                "check that approval records are joined on approved_slot=slot_id"
            )

    def test_m1_approvals_linked_exact(self):
        """approvals_linked counts match the actual approval records per session."""
        _run_audit()
        by_sess = _by_session(_load_report())
        for sid, expected in EXPECTED_APPROVALS.items():
            got = by_sess[sid]["approvals_linked"]
            assert got == expected, f"{sid}: approvals_linked={got}, want {expected}"

    def test_m1_required_fields_present(self):
        """Every report entry contains all required fields."""
        _run_audit()
        required = {
            "session_id",
            "slots_loaded",
            "approvals_linked",
            "reconstruction_status",
            "secret_fingerprint",
            "threshold_met",
            "quorum_valid",
            "policy_violations",
            "verification_status",
        }
        report = _load_report()
        for entry in report["audit_results"]:
            missing = required - set(entry.keys())
            assert not missing, f"Entry {entry.get('session_id')} missing fields: {missing}"

    def test_m1_policy_violations_is_list(self):
        """policy_violations is a list (not null) for every entry."""
        _run_audit()
        report = _load_report()
        for entry in report["audit_results"]:
            assert isinstance(entry["policy_violations"], list), (
                f"Session {entry['session_id']}: policy_violations must be a list"
            )

    def test_m1_approvals_linked_matches_direct_db_query(self):
        """approvals_linked matches a direct SQL query joining approved_slot to slot_id.

        The buggy implementation links approvals via approved_by = custodian_id (wrong column),
        which yields 0 per session.  The correct join is approved_slot = slot_id.
        This test bypasses the tool entirely and verifies counts against the database.
        """
        _run_audit()
        by_sess = _by_session(_load_report())

        conn = sqlite3.connect(DB)
        for sid in EXPECTED_SESSIONS:
            # Ground truth: count distinct slots that have at least one approval
            # referencing them through the correct FK column (approved_slot = slot_id).
            expected = conn.execute(
                """
                SELECT COUNT(DISTINCT sr.slot_id)
                FROM slot_registry sr
                JOIN ceremony_approvals ap ON ap.approved_slot = sr.slot_id
                WHERE sr.session_id = ?
                """,
                (sid,),
            ).fetchone()[0]
            reported = by_sess[sid]["approvals_linked"]
            assert reported == expected, (
                f"{sid}: approvals_linked={reported} but correct SQL join gives {expected}; "
                "check that approvals are linked via ap.approved_slot = sr.slot_id, "
                "not via ap.approved_by = sr.custodian_id"
            )
        conn.close()
