"""Behavioral checks for the trace driver versus the replay model."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

DRIVER = Path("/app/bin/trace_driver")
SRC_ROOT = Path("/app/src")
NO_EMBED_TOKEN = "tb_probe_noembed_z88"


def _run_scenario(ops: list[dict], scenario_id: str, tmp_path: Path) -> dict:
    scenario = {"scenario_id": scenario_id, "ops": ops}
    scen_path = tmp_path / "scenario.json"
    report_path = tmp_path / "report.json"
    scen_path.write_text(json.dumps(scenario), encoding="utf-8")
    subprocess.run(
        [str(DRIVER), str(scen_path), str(report_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return json.loads(report_path.read_text(encoding="utf-8"))


def _assert_aligned(report: dict) -> None:
    assert report.get("aligned") is True, report


def test_replay_tail_idempotent(tmp_path: Path) -> None:
    """After truncating the journal and restarting, replay must match the model (no phantom keys)."""
    ops = [
        {"op": "put", "key": "alpha", "value": "one"},
        {"op": "crash_truncate_journal", "keep_bytes": 0},
        {"op": "restart"},
        {"op": "get", "key": "alpha"},
    ]
    _assert_aligned(_run_scenario(ops, "replay_tail", tmp_path))


def test_pin_point_stability(tmp_path: Path) -> None:
    """Point reads under an active read scope must not pick up later staging writes."""
    ops = [
        {"op": "put", "key": "pkey", "value": "first"},
        {"op": "open_pin"},
        {"op": "put", "key": "pkey", "value": "second"},
        {"op": "get", "key": "pkey"},
    ]
    _assert_aligned(_run_scenario(ops, "pin_point", tmp_path))


def test_obliterate_under_pin(tmp_path: Path) -> None:
    """Tombstones folded into older runs must stay dominant when a read scope opens afterward."""
    ops = [
        {"op": "put", "key": "gone", "value": "v0"},
        {"op": "flush"},
        {"op": "obliterate", "key": "gone"},
        {"op": "flush"},
        {"op": "merge"},
        {"op": "open_pin"},
        {"op": "get", "key": "gone"},
    ]
    _assert_aligned(_run_scenario(ops, "obliterate_pin", tmp_path))


def test_scan_across_tiles_after_merge(tmp_path: Path) -> None:
    """Range reads must omit keys that were removed in a newer run before folding."""
    ops = [
        {"op": "put", "key": "rk", "value": "old"},
        {"op": "flush"},
        {"op": "obliterate", "key": "rk"},
        {"op": "flush"},
        {"op": "merge"},
        {"op": "scan", "start": "rk", "end": "rk"},
    ]
    _assert_aligned(_run_scenario(ops, "scan_merge", tmp_path))


def test_restart_layout_generation(tmp_path: Path) -> None:
    """Metadata generation replayed from the journal after restart must match the model."""
    ops = [
        {"op": "partial_layout_bump", "delta": 6},
        {"op": "restart"},
        {"op": "check_structure"},
    ]
    _assert_aligned(_run_scenario(ops, "layout_gen", tmp_path))


def test_merge_while_pins_open(tmp_path: Path) -> None:
    """A fold executed while a read scope is open must not corrupt visibility after the scope ends."""
    ops = [
        {"op": "put", "key": "rk", "value": "old"},
        {"op": "flush"},
        {"op": "obliterate", "key": "rk"},
        {"op": "flush"},
        {"op": "open_pin"},
        {"op": "merge"},
        {"op": "close_pin"},
        {"op": "get", "key": "rk"},
    ]
    _assert_aligned(_run_scenario(ops, "merge_pin", tmp_path))


def test_on_disk_layout_invariants(tmp_path: Path) -> None:
    """Materialized runs stay sorted on disk; layout replay stays consistent after restart."""
    data = Path("/app/data")
    ops = [
        {"op": "put", "key": "z", "value": "9"},
        {"op": "put", "key": "y", "value": "8"},
        {"op": "flush"},
        {"op": "partial_layout_bump", "delta": 6},
        {"op": "restart"},
        {"op": "check_structure"},
    ]
    report = _run_scenario(ops, "structure_layout", tmp_path)
    _assert_aligned(report)
    tile_files = sorted(data.glob("tile_*.dat"))
    assert tile_files, "expected at least one materialized run file"
    for path in tile_files:
        keys: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            keys.append(line.split("\t", 1)[0])
        assert keys == sorted(keys)


def test_engine_has_no_baked_golden_strings() -> None:
    """Engine sources must not embed verifier-only probe strings."""
    if not SRC_ROOT.is_dir():
        pytest.skip("source tree not mounted")
    for path in SRC_ROOT.rglob("*.cpp"):
        text = path.read_text(encoding="utf-8", errors="replace")
        assert NO_EMBED_TOKEN not in text
    for path in SRC_ROOT.rglob("*.hpp"):
        text = path.read_text(encoding="utf-8", errors="replace")
        assert NO_EMBED_TOKEN not in text


def test_trace_driver_fails_on_missing_arguments() -> None:
    """The driver should exit non-zero when required paths are not provided."""
    proc = subprocess.run([str(DRIVER)], capture_output=True, text=True, check=False)
    assert proc.returncode == 2


def test_trace_report_schema_shape(tmp_path: Path) -> None:
    """Driver output must include the documented top-level fields and agree with the model on a pin read."""
    ops = [
        {"op": "put", "key": "sk", "value": "a"},
        {"op": "open_pin"},
        {"op": "put", "key": "sk", "value": "b"},
        {"op": "get", "key": "sk"},
    ]
    report = _run_scenario(ops, "schema", tmp_path)
    _assert_aligned(report)
    assert "aligned" in report
    assert "scenario_id" in report
    assert "first_mismatch_index" in report
    assert "first_mismatch_kind" in report
    assert "expected" in report
    assert "actual" in report
