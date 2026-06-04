"""Outcome checks for Redis hold pipeline stock audit report."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
OUT = APP / "output"
REPORT = OUT / "stock_audit.json"
AUDIT = APP / "app" / "stock_audit.sh"
ENSURE = APP / "init" / "ensure_redis.sh"

CATALOG = ["Alpha-Unit", "Beta-Crate", "Gamma-Tote"]


def load_opening() -> dict[str, int]:
    catalog_path = APP / "data" / "sku_catalog.json"
    rows = json.loads(catalog_path.read_text(encoding="utf-8"))
    return {row["label"]: row["opening_units"] for row in rows}


OPENING = load_opening()
SCENARIOS = (
    "solo_lane",
    "burst_dual",
    "burst_quad",
    "mixed_skus",
    "zero_floor",
    "pipe_burst",
    "retry_lane",
    "reject_over_cap",
    "gamma_solo",
    "beta_solo",
    "alpha_edge",
    "stress_fan",
    "stagger_race",
    "triple_interleave",
    "unit_rush",
    "two_phase_drain",
    "canonical_drift",
    "odd_remainder",
    "bimodal_burst",
    "saturated_fan",
)

CANONICAL_KEYS = {
    row["label"]: row["key"]
    for row in json.loads((APP / "data" / "sku_catalog.json").read_text(encoding="utf-8"))
}


def run_checked(cmd: list[str], *, timeout: int = 180) -> None:
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(cmd)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def run_audit() -> dict:
    run_checked(["bash", str(ENSURE)])
    OUT.mkdir(parents=True, exist_ok=True)
    run_checked(["bash", str(AUDIT)])
    return json.loads(REPORT.read_text(encoding="utf-8"))


def assert_no_oversell(row: dict, *, opening: int | None = None) -> None:
    assert row["oversell_detected"] is False
    assert row["final_stock"] >= 0
    if opening is not None:
        assert row["total_granted"] <= opening


def assert_conservation(row: dict, *, opening: int) -> None:
    """Granted plus remaining must equal the seeded opening count for single-SKU lanes."""
    assert row["total_granted"] + row["final_stock"] == opening


def redis_get(key: str) -> int:
    result = subprocess.run(
        ["redis-cli", "GET", key],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or "redis-cli GET failed")
    raw = (result.stdout or "").strip()
    return int(raw or "0")


def worker_slot_for_label(label: str) -> str:
    result = subprocess.run(
        ["bash", "-c", f'source /app/lib/k7m/step_w1.sh; step_w1 "{label}"'],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or "step_w1 failed")
    return result.stdout.strip()


@pytest.fixture(scope="module")
def report() -> dict:
    return run_audit()


def test_report_schema_version(report: dict) -> None:
    """Audit report includes a schema_version header."""
    assert "schema_version" in report
    assert isinstance(report["schema_version"], int)


def test_catalog_skus_present(report: dict) -> None:
    """Catalog SKU labels match the three seeded products from the prompt."""
    assert report["catalog_skus"] == CATALOG


def test_all_scenarios_present(report: dict) -> None:
    """Every named scenario row exists in the audit map."""
    for key in SCENARIOS:
        assert key in report["scenarios"]


def test_solo_lane_clean(report: dict) -> None:
    """Single worker on Alpha-Unit stays within the six-unit cap."""
    row = report["scenarios"]["solo_lane"]
    assert_no_oversell(row, opening=OPENING["Alpha-Unit"])
    assert row["total_granted"] > 0


def test_burst_dual_no_oversell(report: dict) -> None:
    """Two parallel workers on Alpha-Unit stay within the catalog opening cap."""
    row = report["scenarios"]["burst_dual"]
    assert_no_oversell(row, opening=OPENING["Alpha-Unit"])


def test_burst_quad_no_oversell(report: dict) -> None:
    """Four parallel workers on Beta-Crate stay within the catalog opening cap."""
    row = report["scenarios"]["burst_quad"]
    assert_no_oversell(row, opening=OPENING["Beta-Crate"])


def test_mixed_skus_isolated(report: dict) -> None:
    """Parallel Alpha-Unit and Gamma-Tote lanes do not oversell their caps combined."""
    row = report["scenarios"]["mixed_skus"]
    assert row["oversell_detected"] is False
    assert row["final_stock"] >= 0
    combined_cap = OPENING["Alpha-Unit"] + OPENING["Gamma-Tote"]
    assert row["total_granted"] <= combined_cap


def test_zero_floor_honored(report: dict) -> None:
    """Gamma-Tote depletion scenario stays within the catalog opening cap."""
    row = report["scenarios"]["zero_floor"]
    assert_no_oversell(row, opening=OPENING["Gamma-Tote"])


def test_pipe_burst_clean(report: dict) -> None:
    """Pipelined burst simulation on Beta-Crate respects the catalog opening cap."""
    row = report["scenarios"]["pipe_burst"]
    assert_no_oversell(row, opening=OPENING["Beta-Crate"])


def test_retry_lane_clean(report: dict) -> None:
    """Retrying workers on Alpha-Unit do not oversell the catalog opening cap."""
    row = report["scenarios"]["retry_lane"]
    assert_no_oversell(row, opening=OPENING["Alpha-Unit"])


def test_reject_over_cap(report: dict) -> None:
    """Requests above available stock do not oversell the Gamma-Tote catalog cap."""
    row = report["scenarios"]["reject_over_cap"]
    assert_no_oversell(row, opening=OPENING["Gamma-Tote"])


def test_no_scenario_oversell(report: dict) -> None:
    """Stress summary and scenario rows agree that no lane exceeded its cap."""
    assert report["stress_summary"]["oversell_events"] == 0
    for key in SCENARIOS:
        row = report["scenarios"][key]
        label = row.get("sku")
        if label in OPENING:
            assert row["total_granted"] <= OPENING[label]


def test_stress_summary_clean(report: dict) -> None:
    """Stress summary covers every scenario row in the matrix."""
    summary = report["stress_summary"]
    assert summary["scenario_count"] == len(SCENARIOS)


def test_compliance_posture(report: dict) -> None:
    """Stock compliance reflects lane-contract binding and frame posture."""
    comp = report["stock_compliance"]
    assert comp["canonical_keys_seeded"] is True
    assert comp["worker_slot_is_alias"] is not True
    assert comp["forward_observation_frame"] is not True


def test_stagger_race_no_oversell(report: dict) -> None:
    """Eight concurrent workers on Alpha-Unit stay within the catalog opening cap."""
    row = report["scenarios"]["stagger_race"]
    assert_no_oversell(row, opening=OPENING["Alpha-Unit"])
    assert_conservation(row, opening=OPENING["Alpha-Unit"])


def test_triple_sku_interleave_clean(report: dict) -> None:
    """All three SKUs contended in one wave stay within their combined opening caps."""
    row = report["scenarios"]["triple_interleave"]
    assert row["oversell_detected"] is False
    assert row["final_stock"] >= 0
    combined_cap = sum(OPENING[label] for label in CATALOG)
    assert row["total_granted"] <= combined_cap


def test_unit_rush_conservation(report: dict) -> None:
    """Ten single-unit requests on Beta-Crate conserve the seeded opening count."""
    row = report["scenarios"]["unit_rush"]
    assert_no_oversell(row, opening=OPENING["Beta-Crate"])
    assert_conservation(row, opening=OPENING["Beta-Crate"])
    assert row["total_granted"] == OPENING["Beta-Crate"]


def test_two_phase_drain_conservation(report: dict) -> None:
    """Back-to-back worker waves on Alpha-Unit conserve units across both phases."""
    row = report["scenarios"]["two_phase_drain"]
    assert_no_oversell(row, opening=OPENING["Alpha-Unit"])
    assert_conservation(row, opening=OPENING["Alpha-Unit"])


def test_worker_canonical_key_aligned(report: dict) -> None:
    """Worker slot keys stay aligned with catalog seed keys after the full audit run."""
    row = report["scenarios"]["canonical_drift"]
    assert_no_oversell(row, opening=OPENING["Beta-Crate"])
    for label in CATALOG:
        canon = redis_get(CANONICAL_KEYS[label])
        worker = redis_get(worker_slot_for_label(label))
        assert canon == worker, f"{label}: seed key {CANONICAL_KEYS[label]} diverged from worker slot"


def test_odd_remainder_bound(report: dict) -> None:
    """Seven dual-unit requests on Beta-Crate cannot exceed the catalog opening cap."""
    row = report["scenarios"]["odd_remainder"]
    assert_no_oversell(row, opening=OPENING["Beta-Crate"])
    assert_conservation(row, opening=OPENING["Beta-Crate"])
    assert row["total_granted"] == OPENING["Beta-Crate"]


def test_bimodal_demand_no_oversell(report: dict) -> None:
    """Mixed small and large request sizes on Gamma-Tote stay within the opening cap."""
    row = report["scenarios"]["bimodal_burst"]
    assert_no_oversell(row, opening=OPENING["Gamma-Tote"])
    assert_conservation(row, opening=OPENING["Gamma-Tote"])


def test_saturated_fan_no_oversell(report: dict) -> None:
    """Twelve single-unit workers on Alpha-Unit cannot overshoot the six-unit opening."""
    row = report["scenarios"]["saturated_fan"]
    assert_no_oversell(row, opening=OPENING["Alpha-Unit"])
    assert_conservation(row, opening=OPENING["Alpha-Unit"])
    assert row["total_granted"] == OPENING["Alpha-Unit"]