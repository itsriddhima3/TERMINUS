"""Milestone 2 — relational move gates for SCN-Alpha."""

import json
import sqlite3
import subprocess
from pathlib import Path

DB = Path("/app/var/game.db")
FLUX = "/app/bin/fluxctl"
SCN = "SCN-Alpha"
ILLEGAL = "/app/data/transcripts/illegal_adj.script"


def _fresh() -> None:
    if DB.exists():
        DB.unlink()
    subprocess.run([FLUX, "init", "--scenario", SCN], check=True, timeout=30)


def _level(row: int, col: int) -> int:
    c = sqlite3.connect(DB)
    val = c.execute(
        "SELECT level FROM components WHERE scenario_id = ? AND row = ? AND col = ?",
        (SCN, row, col),
    ).fetchone()[0]
    c.close()
    return val


def _metrics() -> tuple[int, int, int]:
    proc = subprocess.run([FLUX, "status", "--json"], capture_output=True, text=True, timeout=15)
    doc = json.loads(proc.stdout)
    return doc["metric_a"], doc["metric_b"], doc["metric_c"]


class TestMilestone2:
    def test_m2_reject_adjacent_delta(self):
        """Adjacent same-kind level jump greater than param_a is rejected."""
        _fresh()
        proc = subprocess.run([FLUX, "set", "0", "1", "3"], capture_output=True, text=True, timeout=15)
        assert proc.returncode != 0

    def test_m2_accept_legal_set(self):
        """Delta-zero adjustment on an isolated vent cell succeeds."""
        _fresh()
        before = _level(0, 2)
        proc = subprocess.run([FLUX, "set", "0", "2", str(before)], capture_output=True, text=True, timeout=15)
        assert proc.returncode == 0
        assert _level(0, 2) == before

    def test_m2_enforce_type_max(self):
        """Level above per-kind max from constraints is rejected."""
        _fresh()
        proc = subprocess.run([FLUX, "set", "1", "1", "4"], capture_output=True, text=True, timeout=15)
        assert proc.returncode != 0

    def test_m2_reject_corner_three(self):
        """Corner slot level above corner_cap param is rejected."""
        _fresh()
        proc = subprocess.run([FLUX, "set", "0", "0", "3"], capture_output=True, text=True, timeout=15)
        assert proc.returncode != 0

    def test_m2_priority_order_trap(self):
        """Corner cap fires before type_max allows level three at a corner."""
        _fresh()
        proc = subprocess.run([FLUX, "set", "2", "2", "3"], capture_output=True, text=True, timeout=15)
        assert proc.returncode != 0
        assert _level(2, 2) == 2

    def test_m2_illegal_unchanged_db(self):
        """Failed set leaves the targeted cell level unchanged."""
        _fresh()
        before = _level(0, 1)
        subprocess.run([FLUX, "set", "0", "1", "3"], capture_output=True, timeout=15)
        assert _level(0, 1) == before

    def test_m2_tick_moves_metrics(self):
        """Metrics change only after tick, not after a legal set."""
        _fresh()
        a0, b0, c0 = _metrics()
        subprocess.run([FLUX, "set", "1", "1", "2"], check=True, timeout=15)
        a1, b1, c1 = _metrics()
        assert (a1, b1, c1) == (a0, b0, c0)
        subprocess.run([FLUX, "tick"], check=True, timeout=15)
        a2, b2, c2 = _metrics()
        assert (a2, b2, c2) != (a0, b0, c0)

    def test_m2_script_illegal_exit(self):
        """Bundled illegal transcript exits non-zero."""
        _fresh()
        proc = subprocess.run([FLUX, "run", ILLEGAL], capture_output=True, text=True, timeout=30)
        assert proc.returncode != 0

    def test_m2_delta_one_boundary_accept(self):
        """Adjacent same-kind delta exactly at param_a is accepted (strictly-greater check)."""
        _fresh()
        assert _level(0, 1) == 1
        assert _level(1, 1) == 1
        proc = subprocess.run([FLUX, "set", "0", "1", "2"], capture_output=True, text=True, timeout=15)
        assert proc.returncode == 0, proc.stderr
        assert _level(0, 1) == 2
        assert _level(1, 1) == 1

    def test_m2_rod_chain_legal_then_block(self):
        """Staged rod adjustments succeed until a later jump violates adjacency delta."""
        _fresh()
        subprocess.run([FLUX, "set", "0", "1", "2"], check=True, timeout=15)
        subprocess.run([FLUX, "set", "1", "1", "2"], check=True, timeout=15)
        assert _level(0, 1) == 2 and _level(1, 1) == 2
        proc = subprocess.run([FLUX, "set", "0", "1", "0"], capture_output=True, text=True, timeout=15)
        assert proc.returncode != 0
        assert _level(0, 1) == 2
        assert _level(1, 1) == 2
