"""Verifier for g7render Graphviz batch layout report."""

import json
import re
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
REPORT = APP / "output" / "layout_report.json"
MATRIX = APP / "data" / "workload_matrix.json"
_BUILT = False

def _expected_rows() -> dict[str, dict]:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    return {
        row["workload_id"]: row["acceptance"]
        for row in matrix["workloads"]
    }


@pytest.fixture(scope="session", autouse=True)
def _build_once() -> None:
    global _BUILT
    if _BUILT:
        return
    subprocess.run(["bash", str(APP / "scripts" / "build.sh")], cwd="/app", check=True)
    _BUILT = True


@pytest.fixture(scope="session")
def batch_result() -> subprocess.CompletedProcess[str]:
    if REPORT.exists():
        REPORT.unlink()
    work = APP / "output" / "work"
    if work.exists():
        import shutil

        shutil.rmtree(work)
    return subprocess.run(
        [str(APP / "bin" / "g7render"), "lane"],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="session")
def report(batch_result: subprocess.CompletedProcess[str]) -> dict:
    assert batch_result.returncode == 0, batch_result.stderr
    assert REPORT.is_file(), "layout_report.json missing"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _row(report: dict, workload_id: str) -> dict:
    for entry in report["runs"]:
        if entry["workload_id"] == workload_id:
            return entry
    raise KeyError(workload_id)


def test_report_schema_version(report: dict) -> None:
    """Report carries schema_version 1."""
    assert report["schema_version"] == 1


def test_report_has_two_runs(report: dict) -> None:
    """Both matrix workloads appear exactly once."""
    assert len(report["runs"]) == 2
    ids = {r["workload_id"] for r in report["runs"]}
    assert ids == {"wk-compact", "wk-plateau"}


def test_wk_compact_node_accounting(report: dict) -> None:
    """wk-compact row matches matrix acceptance bands."""
    row = _row(report, "wk-compact")
    exp = _expected_rows()["wk-compact"]
    for key, val in exp.items():
        assert row[key] == val, key


def test_wk_plateau_node_accounting(report: dict) -> None:
    """wk-plateau row matches matrix acceptance bands."""
    row = _row(report, "wk-plateau")
    exp = _expected_rows()["wk-plateau"]
    for key, val in exp.items():
        assert row[key] == val, key


def test_compact_svg_lists_all_core_nodes(report: dict) -> None:
    """Compact render.svg retains every core_* vertex."""
    row = _row(report, "wk-compact")
    svg = Path(row["artifact_svg"])
    assert svg.is_file()
    body = svg.read_text(encoding="utf-8", errors="replace")
    for i in range(84):
        assert f"core_{i}" in body


def test_plateau_svg_excludes_isolated_ids(report: dict) -> None:
    """Plateau render.svg drops iso_* placeholders."""
    row = _row(report, "wk-plateau")
    svg = Path(row["artifact_svg"])
    body = svg.read_text(encoding="utf-8", errors="replace")
    assert "iso_0" not in body
    assert "iso_1199" not in body
    assert "core_0" in body
    assert "core_319" in body


def test_plateau_pruned_dot_has_no_isolated_nodes(report: dict) -> None:
    """Pruned DOT removes degree-zero islands for plateau."""
    pruned = APP / "output" / "work" / "wk-plateau" / "pruned.dot"
    assert pruned.is_file()
    text = pruned.read_text(encoding="utf-8")
    assert "iso_0" not in text
    assert re.search(r"core_\d+\s*\[", text)
    assert text.count("core_") >= 320


def test_raw_plateau_still_contains_isolated_placeholders() -> None:
    """Raw DOT still includes placeholder islands before pruning."""
    raw = APP / "output" / "work" / "wk-plateau" / "raw.dot"
    assert raw.is_file()
    text = raw.read_text(encoding="utf-8")
    assert "iso_0" in text
    assert "iso_1199" in text


def test_layout_engine_uses_sfdp_binary(report: dict) -> None:
    """sparse_scale profile must bind to sfdp per bench_profiles + manual."""
    profiles = (APP / "config" / "bench_profiles.toml").read_text(encoding="utf-8")
    assert 'engine_binary = "sfdp"' in profiles
    for wid in ("wk-compact", "wk-plateau"):
        row = _row(report, wid)
        svg = Path(row["artifact_svg"]).read_text(encoding="utf-8", errors="replace")
        assert len(svg) > 200
        assert "<svg" in svg


def test_prune_pass_not_noop_on_plateau(report: dict) -> None:
    """Plateau accounting reflects a real isolation pass."""
    row = _row(report, "wk-plateau")
    assert row["prune_pass_applied"] is True
    raw_nodes = row["input_nodes"]
    out_nodes = row["output_nodes"]
    assert raw_nodes - out_nodes == row["isolated_removed"]


def test_matrix_rows_match_report_ids(report: dict) -> None:
    """Report workloads mirror the matrix file."""
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    matrix_ids = {w["workload_id"] for w in matrix["workloads"]}
    report_ids = {r["workload_id"] for r in report["runs"]}
    assert matrix_ids == report_ids
