"""Verifier for lane audit JSON."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
OUT = APP / "output"
REPORT = OUT / "lane_audit.json"
AUDIT = APP / "app" / "lane_audit.sh"
ENSURE = APP / "init" / "ensure_pg.sh"
START = APP / "init" / "start_api.sh"

CAPS = {
    "North-Shelf": 6,
    "East-Crate": 10,
    "West-Bin": 4,
}
PARTITIONS = ["North-Shelf", "East-Crate", "West-Bin"]
SCENARIOS = (
    "w1_single",
    "w2_pair",
    "w4_quad",
    "mix_parallel",
    "deplete_exact",
    "pipe_backlog",
    "idempotent_rerun",
    "over_cap_reject",
    "interleave_ab",
    "partial_abort",
    "stamp_guard",
    "post_write_snap",
    "sibling_contention",
    "pool_dual_conn",
    "parity_probe",
    "biz_key_race",
    "rollup_seq_m",
    "rollup_seq_n",
    "rollup_seq_o",
    "rollup_seq_p",
    "tri_fanout",
    "solo_west",
)


def run_checked(cmd: list[str], *, timeout: int = 300) -> None:
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    if proc.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(cmd)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )


def run_audit() -> dict:
    run_checked(["bash", str(ENSURE)])
    run_checked(["bash", str(START)])
    OUT.mkdir(parents=True, exist_ok=True)
    run_checked(["bash", str(AUDIT)], timeout=600)
    return json.loads(REPORT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def report() -> dict:
    return run_audit()


def test_v1_field(report: dict) -> None:
    """Audit report declares schema version 1."""
    assert report["schema_version"] == 1


def test_label_order(report: dict) -> None:
    """Catalog partition labels list the three shelf families in order."""
    assert report["catalog_partitions"] == PARTITIONS


def test_slots_complete(report: dict) -> None:
    """All twenty-two scenario keys from the matrix appear in the report."""
    for name in SCENARIOS:
        assert name in report["scenarios"]


def test_w1_single(report: dict) -> None:
    """Single worker on North-Shelf ingests three chunks with no lost rows."""
    row = report["scenarios"]["w1_single"]
    assert row["lost_rows"] == 0
    assert row["chunks_attempted"] == 3


def test_w2_pair(report: dict) -> None:
    """Two parallel workers on North-Shelf stay within cap without duplicate keys."""
    row = report["scenarios"]["w2_pair"]
    assert row["duplicate_external_keys"] == 0
    assert row["unstable_totals"] is False


def test_w4_quad(report: dict) -> None:
    """Four workers on East-Crate honor the ten-slot cap with stable totals."""
    row = report["scenarios"]["w4_quad"]
    assert row["unstable_totals"] is False


def test_mix_ok(report: dict) -> None:
    """Parallel North and West workers do not cross-taint rollup totals."""
    row = report["scenarios"]["mix_parallel"]
    assert row["unstable_totals"] is False


def test_deplete_ok(report: dict) -> None:
    """Exact family depletion leaves stable totals without duplicate keys."""
    row = report["scenarios"]["deplete_exact"]
    assert row["duplicate_external_keys"] == 0
    assert row["unstable_totals"] is False


def test_backlog_ok(report: dict) -> None:
    """Pipelined chunk simulation stays within caps with stable totals."""
    row = report["scenarios"]["pipe_backlog"]
    assert row["unstable_totals"] is False


def test_rerun_ok(report: dict) -> None:
    """Replaying workers do not double-insert business keys."""
    row = report["scenarios"]["idempotent_rerun"]
    assert row["duplicate_external_keys"] == 0


def test_cap_reject(report: dict) -> None:
    """Chunks above family cap report zero loss without negative totals."""
    row = report["scenarios"]["over_cap_reject"]
    assert row["lost_rows"] == 0


def test_no_loss(report: dict) -> None:
    """Every scenario row reports zero lost rows."""
    for name in SCENARIOS:
        assert report["scenarios"][name]["lost_rows"] == 0


def test_global_ok(report: dict) -> None:
    """Stress summary reports zero loss events when the matrix is clean."""
    assert report["stress_summary"]["loss_events"] == 0


def test_interleave_ab(report: dict) -> None:
    """Alternating bursts across North-Shelf and East-Crate keep parity and stable totals."""
    row = report["scenarios"]["interleave_ab"]
    assert row["unstable_totals"] is False
    assert row["line_parity_ok"] is True


def test_partial_abort_ok(report: dict) -> None:
    """Mid-chunk fault leaves zero loss and line parity without orphan headers."""
    row = report["scenarios"]["partial_abort"]
    assert row["line_parity_ok"] is True
    assert row["lost_rows"] == 0


def test_stamp_diverge_guard(report: dict) -> None:
    """Divergent replays on the same business key produce no duplicate keys."""
    row = report["scenarios"]["stamp_guard"]
    assert row["duplicate_external_keys"] == 0


def test_snapshot_consistent(report: dict) -> None:
    """Post-write snapshot includes lines from the just-accepted chunk."""
    row = report["scenarios"]["post_write_snap"]
    assert row["read_after_write_ok"] is True


def test_contention_sibling(report: dict) -> None:
    """Concurrent quad East and solo North lanes both keep stable totals."""
    row = report["scenarios"]["sibling_contention"]
    assert row["unstable_totals"] is False


def test_pool_handoff_ok(report: dict) -> None:
    """Sequential chunks on distinct pool connections avoid phantom rollup drift."""
    row = report["scenarios"]["pool_dual_conn"]
    assert row["unstable_totals"] is False


def test_line_parity_matrix(report: dict) -> None:
    """Every scenario row reports line parity between accepted and persisted counts."""
    for name in SCENARIOS:
        assert report["scenarios"][name]["line_parity_ok"] is True


def test_race_one_winner(report: dict) -> None:
    """Simultaneous posts for the same business key yield a single winner row."""
    row = report["scenarios"]["biz_key_race"]
    assert row["duplicate_external_keys"] == 0


def test_monotone_counter(report: dict) -> None:
    """Ordered rollup sequence scenarios keep monotone counters."""
    for name in ("rollup_seq_m", "rollup_seq_n", "rollup_seq_o", "rollup_seq_p"):
        assert report["scenarios"][name]["rollup_monotone"] is True


def test_tri_fanout_ok(report: dict) -> None:
    """Three-family simultaneous burst honors caps with ingest compliance true."""
    row = report["scenarios"]["tri_fanout"]
    assert row["unstable_totals"] is False
    assert report["ingest_compliance"] is True
