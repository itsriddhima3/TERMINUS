"""Milestone 3 — playthrough outcome, persistence, and transcripts."""

import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

DB = Path("/app/var/game.db")
FLUX = "/app/bin/fluxctl"
SCN = "SCN-Alpha"
WIN = "/app/data/transcripts/win_alpha.script"


def _fresh() -> None:
    if DB.exists():
        DB.unlink()
    subprocess.run([FLUX, "init", "--scenario", SCN], check=True, timeout=30)


def _status() -> dict:
    proc = subprocess.run([FLUX, "status", "--json"], capture_output=True, text=True, timeout=15)
    assert proc.returncode == 0
    return json.loads(proc.stdout)


class TestMilestone3:
    def test_m3_win_script_zero(self):
        """Winning transcript exits zero with victory flag set."""
        _fresh()
        proc = subprocess.run([FLUX, "run", WIN], capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0
        doc = json.loads(proc.stdout)
        assert doc["won"] is True

    def test_m3_stable_three_ticks(self):
        """Victory requires stable streak of three."""
        _fresh()
        subprocess.run([FLUX, "run", WIN], check=True, timeout=60)
        doc = _status()
        assert doc["stable_streak"] >= 3

    def test_m3_save_load_streak(self):
        """Named slot reload restores stable streak counter."""
        _fresh()
        for _ in range(2):
            subprocess.run([FLUX, "tick"], check=True, timeout=15)
        streak_before = _status()["stable_streak"]
        subprocess.run([FLUX, "save", "mid"], check=True, timeout=15)
        subprocess.run([FLUX, "tick"], check=True, timeout=15)
        subprocess.run([FLUX, "load", "mid"], check=True, timeout=15)
        doc = _status()
        assert doc["stable_streak"] == streak_before

    def test_m3_loss_breach(self):
        """Loss triggers at configured breach threshold, not band upper bound."""
        _fresh()
        subprocess.run([FLUX, "set", "0", "0", "2"], check=True, timeout=15)
        subprocess.run([FLUX, "set", "2", "2", "2"], check=True, timeout=15)
        for _ in range(12):
            subprocess.run([FLUX, "tick"], check=True, timeout=15)
            doc = _status()
            if doc["lost"]:
                break
        doc = _status()
        assert doc["lost"] is True
        assert doc["metric_a"] >= 100 or doc["metric_b"] >= 100 or doc["metric_c"] >= 100

    def test_m3_resume_win_path(self):
        """Save before final ticks, load, then finish victory."""
        _fresh()
        cmds = [
            [FLUX, "set", "0", "0", "0"],
            [FLUX, "set", "0", "1", "0"],
            [FLUX, "set", "0", "2", "0"],
            [FLUX, "set", "1", "0", "0"],
            [FLUX, "set", "1", "1", "0"],
            [FLUX, "set", "1", "2", "0"],
            [FLUX, "set", "2", "0", "0"],
            [FLUX, "set", "2", "1", "0"],
            [FLUX, "set", "2", "2", "0"],
            [FLUX, "tick"],
            [FLUX, "tick"],
        ]
        for cmd in cmds:
            subprocess.run(cmd, check=True, timeout=15)
        subprocess.run([FLUX, "save", "resume"], check=True, timeout=15)
        subprocess.run([FLUX, "tick"], check=True, timeout=15)
        subprocess.run([FLUX, "load", "resume"], check=True, timeout=15)
        subprocess.run([FLUX, "tick"], check=True, timeout=15)
        doc = _status()
        assert doc["won"] is True

    def test_m3_status_json_complete(self):
        """Status JSON exposes scenario, tick, metrics, streak, flags, grid."""
        _fresh()
        doc = _status()
        for key in (
            "scenario",
            "tick",
            "metric_a",
            "metric_b",
            "metric_c",
            "stable_streak",
            "won",
            "lost",
            "schema_version",
            "grid",
        ):
            assert key in doc
        assert len(doc["grid"]) == 3
        assert len(doc["grid"][0]) == 3

    def test_m3_script_hash_stable(self):
        """Win transcript output hash is deterministic."""
        _fresh()
        proc1 = subprocess.run([FLUX, "run", WIN], capture_output=True, text=True, timeout=60)
        h1 = hashlib.sha256(proc1.stdout.encode()).hexdigest()
        _fresh()
        proc2 = subprocess.run([FLUX, "run", WIN], capture_output=True, text=True, timeout=60)
        h2 = hashlib.sha256(proc2.stdout.encode()).hexdigest()
        assert h1 == h2

    def test_m3_mid_save_levels(self):
        """Save/load preserves cell levels mid-run."""
        _fresh()
        subprocess.run([FLUX, "set", "1", "1", "1"], check=True, timeout=15)
        subprocess.run([FLUX, "save", "lv"], check=True, timeout=15)
        subprocess.run([FLUX, "set", "1", "1", "0"], check=True, timeout=15)
        subprocess.run([FLUX, "load", "lv"], check=True, timeout=15)
        c = sqlite3.connect(DB)
        lvl = c.execute(
            "SELECT level FROM components WHERE scenario_id = ? AND row = 1 AND col = 1",
            (SCN,),
        ).fetchone()[0]
        c.close()
        assert lvl == 1

    def test_m3_no_victory_before_stable_needed(self):
        """A single in-band tick must not declare victory when stable_needed is three."""
        _fresh()
        for row, col in ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)):
            subprocess.run([FLUX, "set", str(row), str(col), "0"], check=True, timeout=15)
        subprocess.run([FLUX, "tick"], check=True, timeout=15)
        doc = _status()
        assert doc["metric_a"] == 55 and doc["metric_b"] == 45 and doc["metric_c"] == 35
        assert doc["stable_streak"] == 1
        assert doc["won"] is False
        assert doc["lost"] is False

    def test_m3_streak_reset_after_drift(self):
        """Stable streak resets to zero when a tick pushes metrics outside bands."""
        _fresh()
        for row, col in ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)):
            subprocess.run([FLUX, "set", str(row), str(col), "0"], check=True, timeout=15)
        subprocess.run([FLUX, "tick"], check=True, timeout=15)
        subprocess.run([FLUX, "tick"], check=True, timeout=15)
        assert _status()["stable_streak"] == 2
        subprocess.run([FLUX, "set", "0", "0", "2"], check=True, timeout=15)
        subprocess.run([FLUX, "set", "2", "2", "2"], check=True, timeout=15)
        subprocess.run([FLUX, "tick"], check=True, timeout=15)
        doc = _status()
        assert doc["metric_a"] > 60
        assert doc["stable_streak"] == 0
        assert doc["won"] is False
