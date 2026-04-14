"""Verifiers for implicit integrator restart outputs (behavioral checks on JSON artifacts)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

REPORT = Path("/app/out/restart_report.json")
AUDIT = Path("/app/out/persistence_audit.log")
GOLDEN_A = Path("/tests/golden/uninterrupted_A.jsonl")
GOLDEN_B = Path("/tests/golden/uninterrupted_B.jsonl")
GOLDEN_C = Path("/tests/golden/uninterrupted_C.jsonl")
DEFAULT_TOML = Path("/app/data/default.toml")
SNAPSHOT = Path("/app/work/snapshot.bin")


def fnv1a64(s: str) -> int:
    h = 14695981039346656037
    prime = 1099511628211
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * prime) & 0xFFFFFFFFFFFFFFFF
    return h


def parse_default_toml(path: Path) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    cur = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            cur = line[1:-1].strip()
            sections.setdefault(cur, {})
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            sections.setdefault(cur, {})[k.strip()] = v.strip()
    return sections


def fingerprint_from_parsed(sec: dict[str, dict[str, str]]) -> str:
    def arr3(key: str) -> tuple[float, float, float]:
        raw = sec["mass"]["diagonal"].strip("[]")
        parts = [float(x.strip()) for x in raw.split(",") if x.strip()]
        assert len(parts) == 3
        return parts[0], parts[1], parts[2]

    m0, m1, m2 = arr3("diagonal")
    k0 = float(sec["model"]["k0"])
    k1 = float(sec["model"]["k1"])
    k2 = float(sec["model"]["k2"])
    gamma = float(sec["butcher"]["gamma"])
    damp = float(sec["discretization"]["stability_extra_damping"])
    return (
        f"M:{m0:.17f},{m1:.17f},{m2:.17f}"
        f"|k0:{k0:.17f}|k1:{k1:.17f}|k2:{k2:.17f}"
        f"|gamma:{gamma:.17f}|damp:{damp:.17f}"
    )


def load_report() -> dict:
    assert REPORT.is_file(), "missing /app/out/restart_report.json — build and run the harness first"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def parse_golden(path: Path) -> tuple[list[dict], dict]:
    steps: list[dict] = []
    summary: dict = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        k = row.get("kind")
        if k == "step":
            steps.append(row)
        elif k == "summary":
            summary = row
    assert summary, f"no summary line in {path}"
    return steps, summary


def relclose(a: float, b: float, rtol: float = 1e-6, atol: float = 1e-7) -> bool:
    return abs(a - b) <= max(atol, rtol * max(abs(a), abs(b), 1.0))


@pytest.fixture(scope="module")
def rep() -> dict:
    return load_report()


@pytest.fixture(scope="module")
def sec() -> dict[str, dict[str, str]]:
    return parse_default_toml(DEFAULT_TOML)


def test_restart_report_schema(rep: dict) -> None:
    """Top-level JSON exposes checksum, probes, and three schedule blocks."""
    assert "operator_signature_checksum" in rep
    assert "integrity_probes" in rep
    ip = rep["integrity_probes"]
    assert ip.get("stale_operator_bundle_rejected") is True
    assert ip.get("stale_damping_bundle_rejected") is True
    for k in ("A", "B", "C"):
        assert k in rep["schedules"]


def test_operator_checksum_matches_config(rep: dict, sec: dict[str, dict[str, str]]) -> None:
    """Checksum matches the same FNV string the integrator documents for the bundled TOML."""
    fp = fingerprint_from_parsed(sec)
    assert rep["operator_signature_checksum"] == fnv1a64(fp)


def test_mass_matrix_not_identity(sec: dict[str, dict[str, str]]) -> None:
    """Mass diagonal from config is not the identity; wrong mass choice breaks trajectory parity."""
    raw = sec["mass"]["diagonal"].strip("[]")
    vals = [float(x.strip()) for x in raw.split(",") if x.strip()]
    assert len(vals) == 3
    assert not math.isclose(vals[0], 1.0) or not math.isclose(vals[1], 1.0) or not math.isclose(vals[2], 1.0)


def test_schedule_parity_against_golden_a(rep: dict) -> None:
    """Schedule A matches the golden stream for steps, final state, and acceptance counts."""
    steps, summary = parse_golden(GOLDEN_A)
    sch = rep["schedules"]["A"]
    assert sch["ok"] is True
    assert sch["accepted_steps"] == summary["accepted_steps"]
    assert sch["rejected_steps"] == summary["rejected_steps"]
    last = steps[-1]
    assert relclose(sch["final_time"], last["t"])
    for i in range(3):
        assert relclose(sch["final_state"][i], last["y"][i])
    if summary.get("event_time") is not None:
        assert sch["event_time"] is not None
        assert relclose(sch["event_time"], float(summary["event_time"]), atol=5e-7)
    else:
        assert sch["event_time"] is None


def test_schedule_parity_against_golden_b(rep: dict) -> None:
    """Schedule B (event shrink interrupt) reproduces the reference stream."""
    steps, summary = parse_golden(GOLDEN_B)
    sch = rep["schedules"]["B"]
    assert sch["ok"] is True
    assert sch["accepted_steps"] == summary["accepted_steps"]
    last = steps[-1]
    assert relclose(sch["final_time"], last["t"])
    for i in range(3):
        assert relclose(sch["final_state"][i], last["y"][i])


def test_schedule_parity_against_golden_c(rep: dict) -> None:
    """Schedule C (mid-stage resume) stays aligned with the golden summary."""
    steps, summary = parse_golden(GOLDEN_C)
    sch = rep["schedules"]["C"]
    assert sch["ok"] is True
    assert sch["accepted_steps"] == summary["accepted_steps"]
    last = steps[-1]
    assert relclose(sch["final_time"], last["t"])
    for i in range(3):
        assert relclose(sch["final_state"][i], last["y"][i])


def test_newton_work_cap_each_schedule(rep: dict) -> None:
    """Post-restart Newton totals stay within the documented budget versus each golden reference."""
    for key, path in (("A", GOLDEN_A), ("B", GOLDEN_B), ("C", GOLDEN_C)):
        _, summary = parse_golden(path)
        n_ref = int(summary["newton_iterations"])
        n_run = int(rep["schedules"][key]["newton_iterations"])
        assert n_run <= 1.35 * n_ref + 8.0


def test_persistence_audit_mentions_snapshot(rep: dict) -> None:
    """Audit log records load attempts for the workspace bundle path."""
    text = AUDIT.read_text(encoding="utf-8")
    assert str(SNAPSHOT) in text
    assert "ACCEPTED" in text
    assert "REJECTED" in text and "SIGNATURE_MISMATCH" in text


def test_all_schedules_marked_ok(rep: dict) -> None:
    """Aggregator: every schedule completes successfully in the combined report."""
    for k in ("A", "B", "C"):
        assert rep["schedules"][k]["ok"] is True


def test_no_trailing_corrupt_json(rep: dict) -> None:
    """Restart report is single-object JSON (parseable once)."""
    raw = REPORT.read_text(encoding="utf-8").strip()
    assert raw.endswith("}")
    json.loads(raw)
