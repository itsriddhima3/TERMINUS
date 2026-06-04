"""Outcome checks for Go fan-out synchronization audit report."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
OUT = APP / "output"
REPORT = OUT / "sync_audit.json"
AUDIT = APP / "app" / "sync_audit.sh"
MATRIX = APP / "data" / "scenario_matrix.json"

ADVANCED = (
    "fanout_triple",
    "mid_detach",
    "branch_toggle",
    "drain_zero_edge",
    "relay_sidecar",
    "coalesce_trace",
    "registry_grow",
    "ack_barrier",
    "ring_rotate",
)


def run_checked(cmd: list[str], *, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(cmd)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def load_matrix() -> dict:
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def base_rows(matrix: dict) -> dict[str, int]:
    return matrix["base_rows"]


def run_audit() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    run_checked(["bash", str(AUDIT)])
    return json.loads(REPORT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def report() -> dict:
    return run_audit()


@pytest.fixture(scope="module")
def matrix() -> dict:
    return load_matrix()


def test_report_schema_version(report: dict) -> None:
    """Report declares schema_version 1."""
    assert report["schema_version"] == 1


def test_all_scenarios_present(report: dict, matrix: dict) -> None:
    """Report includes every base and advanced scenario row plus stress_summary."""
    assert "stress_summary" in report
    keys = list(base_rows(matrix).keys()) + list(ADVANCED)
    for key in keys:
        assert key in report["scenarios"]


def test_burst_delivery_no_stale(report: dict, matrix: dict) -> None:
    """burst_delivery observes matrix base revision without stale_read."""
    exp = base_rows(matrix)["burst_delivery"]
    row = report["scenarios"]["burst_delivery"]
    assert row["expected_revision"] == exp
    assert row["observed_revision"] == exp
    assert row["stale_read"] is False


def test_graceful_stop_no_stale(report: dict, matrix: dict) -> None:
    """graceful_stop observes matrix base revision without stale_read."""
    exp = base_rows(matrix)["graceful_stop"]
    row = report["scenarios"]["graceful_stop"]
    assert row["expected_revision"] == exp
    assert row["observed_revision"] == exp
    assert row["stale_read"] is False


def test_late_attach_no_stale(report: dict, matrix: dict) -> None:
    """late_attach observes matrix base revision without stale_read."""
    exp = base_rows(matrix)["late_attach"]
    row = report["scenarios"]["late_attach"]
    assert row["expected_revision"] == exp
    assert row["observed_revision"] == exp
    assert row["stale_read"] is False


def test_backlog_clear_no_stale(report: dict, matrix: dict) -> None:
    """backlog_clear observes matrix base revision without stale_read."""
    exp = base_rows(matrix)["backlog_clear"]
    row = report["scenarios"]["backlog_clear"]
    assert row["expected_revision"] == exp
    assert row["observed_revision"] == exp
    assert row["stale_read"] is False


def test_no_scenario_stale_reads(report: dict) -> None:
    """No scenario row reports stale_read true."""
    for row in report["scenarios"].values():
        assert row["stale_read"] is False


def test_race_build_clean() -> None:
    """go test -race ./... exits zero from /app."""
    result = run_checked(["go", "test", "-race", "./..."], timeout=600)
    assert result.returncode == 0


def test_seq_monotonic_triple_fanout(report: dict, matrix: dict) -> None:
    """fanout_triple matches matrix revision and seq_monotonic invariant."""
    row = report["scenarios"]["fanout_triple"]
    spec = matrix["advanced_rows"]["fanout_triple"]
    assert row["expected_revision"] == spec["expected_revision"]
    assert row["observed_revision"] == spec["expected_revision"]
    assert row["seq_monotonic"] is spec["seq_monotonic"]
    assert row["stale_read"] is False


def test_mid_detach_peer_isolated(report: dict, matrix: dict) -> None:
    """mid_detach keeps detached peer frozen per matrix."""
    row = report["scenarios"]["mid_detach"]
    spec = matrix["advanced_rows"]["mid_detach"]
    assert row["expected_revision"] == spec["expected_revision"]
    assert row["observed_revision"] == spec["expected_revision"]
    assert row["detached_peer_frozen"] == spec["detached_peer_frozen"]
    assert row["stale_read"] is False


def test_nested_branch_toggle_clean(report: dict, matrix: dict) -> None:
    """branch_toggle ends at matrix expected revision without stale_read."""
    row = report["scenarios"]["branch_toggle"]
    spec = matrix["advanced_rows"]["branch_toggle"]
    assert row["expected_revision"] == spec["expected_revision"]
    assert row["observed_revision"] == spec["expected_revision"]
    assert row["stale_read"] is False


def test_closed_channel_zero_slot_clean(report: dict, matrix: dict) -> None:
    """drain_zero_edge avoids zero_slot_confused per matrix."""
    row = report["scenarios"]["drain_zero_edge"]
    spec = matrix["advanced_rows"]["drain_zero_edge"]
    assert row["expected_revision"] == spec["expected_revision"]
    assert row["zero_slot_confused"] is spec["zero_slot_confused"]
    assert row["stale_read"] is False


def test_metrics_relay_sidecar_intact(report: dict, matrix: dict) -> None:
    """relay_sidecar preserves metrics_ok from matrix."""
    row = report["scenarios"]["relay_sidecar"]
    spec = matrix["advanced_rows"]["relay_sidecar"]
    assert row["expected_revision"] == spec["expected_revision"]
    assert row["metrics_ok"] is spec["metrics_ok"]
    assert row["stale_read"] is False


def test_idle_coalesce_log_intact(report: dict, matrix: dict) -> None:
    """coalesce_trace records matrix coalesce_events without stale_read."""
    row = report["scenarios"]["coalesce_trace"]
    spec = matrix["advanced_rows"]["coalesce_trace"]
    assert row["expected_revision"] == spec["expected_revision"]
    assert row["coalesce_events"] == spec["coalesce_events"]
    assert row["stale_read"] is False


def test_registry_grow_under_load(report: dict, matrix: dict) -> None:
    """registry_grow reports matrix slot_count_delta without stale_read."""
    row = report["scenarios"]["registry_grow"]
    spec = matrix["advanced_rows"]["registry_grow"]
    assert row["expected_revision"] == spec["expected_revision"]
    assert row["slot_count_delta"] == spec["slot_count_delta"]
    assert row["stale_read"] is False


def test_pending_ack_barrier_clean(report: dict, matrix: dict) -> None:
    """ack_barrier hits matrix barrier_hits without stale_read."""
    row = report["scenarios"]["ack_barrier"]
    spec = matrix["advanced_rows"]["ack_barrier"]
    assert row["expected_revision"] == spec["expected_revision"]
    assert row["barrier_hits"] == spec["barrier_hits"]
    assert row["stale_read"] is False


def test_ring_slot_visibility_clean(report: dict, matrix: dict) -> None:
    """ring_rotate exposes matrix slot_index and body_digest."""
    row = report["scenarios"]["ring_rotate"]
    spec = matrix["advanced_rows"]["ring_rotate"]
    assert row["expected_revision"] == spec["expected_revision"]
    assert row["slot_index"] == spec["slot_index"]
    assert row["body_digest"] == spec["body_digest"]
    assert row["stale_read"] is False


def test_hub_packages_detector_clean(report: dict, matrix: dict) -> None:
    """stress_summary matches matrix race_exit_code and iterations_clean."""
    stress = report["stress_summary"]
    spec = matrix["stress_summary"]
    assert stress["race_exit_code"] == spec["race_exit_code"]
    assert stress["iterations_clean"] == spec["iterations_clean"]
