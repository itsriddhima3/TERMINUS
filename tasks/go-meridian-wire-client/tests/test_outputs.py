"""Verifier for Meridian wire client compliance audit."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
OUT = APP / "output" / "wire_audit.json"
AUDIT = APP / "app" / "compliance_audit.sh"
MATRIX = APP / "data" / "scenario_matrix.json"


def run_checked(cmd: list[str], *, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(cmd)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def load_matrix() -> dict:
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def run_audit() -> dict:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    run_checked(["bash", str(AUDIT)])
    return json.loads(OUT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def report() -> dict:
    return run_audit()


@pytest.fixture(scope="module")
def matrix() -> dict:
    return load_matrix()


def row(report: dict, key: str) -> dict:
    assert key in report["scenarios"]
    return report["scenarios"][key]


def test_schema_version(report: dict) -> None:
    """Report declares schema_version 1."""
    assert report["schema_version"] == 1


def test_catalog_scenarios_present(report: dict, matrix: dict) -> None:
    """Every key in scenario_matrix appears in output."""
    for key in matrix["scenarios"]:
        assert key in report["scenarios"]


def test_solo_lane_single_post(report: dict) -> None:
    """Single-threaded Acme-Origin transfer posts once and completes."""
    r = row(report, "scenario_a")
    assert r["completed"] is True
    assert r["duplicate_postings"] is False
    assert r["final_settlement_count"] == 1


def test_burst_fan_one_posting(report: dict) -> None:
    """Four concurrent workers on same intent yield one settlement."""
    r = row(report, "scenario_b")
    assert r["duplicate_postings"] is False
    assert r["final_settlement_count"] == 1
    assert r["completed"] is True


def test_rate_limit_eventually_succeeds(report: dict) -> None:
    """429 with delta-seconds Retry-After eventually completes."""
    r = row(report, "scenario_c")
    assert r["completed"] is True
    assert r["attempts"] >= 2
    assert r["compliance_ok"] is True


def test_http_date_retry_after(report: dict) -> None:
    """503 with HTTP-date Retry-After eventually completes."""
    r = row(report, "scenario_d")
    assert r["completed"] is True
    assert r["attempts"] >= 2
    assert r["compliance_ok"] is True


def test_reuse_within_window(report: dict) -> None:
    """Second attempt within reuse window reuses token without duplicate posting."""
    r = row(report, "scenario_e")
    assert r["completed"] is True
    assert r["duplicate_postings"] is False
    assert r["final_settlement_count"] == 1


def test_expired_key_rotates(report: dict) -> None:
    """Post-expiry attempt mints new token without duplicating prior settlement."""
    r = row(report, "scenario_f")
    assert r["completed"] is True
    assert r["duplicate_postings"] is False
    assert r["final_settlement_count"] <= 1


def test_cross_intent_isolation(report: dict) -> None:
    """Concurrent distinct beneficiary intents do not cross-post."""
    r = row(report, "scenario_g")
    assert r["completed"] is True
    assert r["duplicate_postings"] is False
    assert r["compliance_ok"] is True


def test_mixed_amounts_isolated(report: dict) -> None:
    """Same account, different amounts stay distinct."""
    r = row(report, "scenario_h")
    assert r["completed"] is True
    assert r["duplicate_postings"] is False
    assert r["compliance_ok"] is True


def test_hidden_burst_clean(report: dict) -> None:
    """Hidden burst scenario reports compliance_ok true."""
    r = row(report, "scenario_i")
    assert r["compliance_ok"] is True
    assert r["duplicate_postings"] is False


def test_global_audit_clean(report: dict) -> None:
    """All rows compliance_ok true with zero duplicate_postings."""
    for key, r in report["scenarios"].items():
        assert r["compliance_ok"] is True, key
        assert r["duplicate_postings"] is False, key


def test_escalating_429_staircase(report: dict) -> None:
    """Increasing delta-seconds Retry-After steps; attempts at least 3."""
    r = row(report, "scenario_k")
    assert r["completed"] is True
    assert r["attempts"] >= 3
    assert r["compliance_ok"] is True


def test_probe_commit_shared_token(report: dict) -> None:
    """Probe and commit phases share outbound_token with one settlement."""
    r = row(report, "scenario_l")
    assert r["completed"] is True
    assert r["outbound_token"] != ""
    assert r["final_settlement_count"] == 1
    assert r["duplicate_postings"] is False


def test_anchor_clock_from_acceptance(report: dict) -> None:
    """Delayed retry reuses token when acceptance anchor still valid."""
    r = row(report, "scenario_m")
    assert r["completed"] is True
    assert r["attempts"] >= 2
    assert r["duplicate_postings"] is False
    assert r["compliance_ok"] is True


def test_beneficiary_normalization_hash(report: dict) -> None:
    """gamma_spaced and gamma_compact share settlement; gamma_alt isolated."""
    r = row(report, "scenario_n")
    assert r["completed"] is True
    assert r["duplicate_postings"] is False
    assert r["compliance_ok"] is True


def test_mixed_code_429_then_503(report: dict) -> None:
    """429 then 503 with mixed header formats before success."""
    r = row(report, "scenario_o")
    assert r["completed"] is True
    assert r["attempts"] >= 3
    assert r["compliance_ok"] is True


def test_eight_worker_race(report: dict) -> None:
    """Eight concurrent workers produce a single settlement."""
    r = row(report, "scenario_p")
    assert r["duplicate_postings"] is False
    assert r["final_settlement_count"] == 1
    assert r["completed"] is True


def test_minor_unit_fingerprint(report: dict) -> None:
    """delta_cents and delta_major_alias do not merge."""
    r = row(report, "scenario_q")
    assert r["completed"] is True
    assert r["duplicate_postings"] is False
    assert r["compliance_ok"] is True


def test_precedence_errata_window(report: dict) -> None:
    """Reuse honors precedence memo over volume 04 errata TTL."""
    r = row(report, "scenario_r")
    assert r["completed"] is True
    assert r["duplicate_postings"] is False
    assert r["final_settlement_count"] == 1
    assert r["compliance_ok"] is True
