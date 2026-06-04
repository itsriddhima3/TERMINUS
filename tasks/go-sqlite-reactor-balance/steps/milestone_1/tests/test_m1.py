"""Milestone 1 — SQLite catalog bootstrap for SCN-Alpha."""

import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

DB = Path("/app/var/game.db")
FLUX = "/app/bin/fluxctl"
SCN = "SCN-Alpha"
OPEN = (55, 45, 35)
EXPECTED_LEVELS = {
    (0, 0): 2,
    (0, 1): 1,
    (0, 2): 1,
    (1, 0): 1,
    (1, 1): 1,
    (1, 2): 1,
    (2, 0): 1,
    (2, 1): 1,
    (2, 2): 2,
}


def _reset_db() -> None:
    if DB.exists():
        DB.unlink()


def _init() -> subprocess.CompletedProcess:
    _reset_db()
    return subprocess.run(
        [FLUX, "init", "--scenario", SCN],
        capture_output=True,
        text=True,
        timeout=30,
    )


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(DB)


def _catalog_fingerprint() -> str:
    c = _conn()
    chunks = [
        json.dumps(c.execute("SELECT * FROM meta ORDER BY key").fetchall()),
        json.dumps(
            c.execute(
                "SELECT * FROM chambers WHERE scenario_id = ? ORDER BY row, col",
                (SCN,),
            ).fetchall()
        ),
        json.dumps(
            c.execute(
                "SELECT * FROM components WHERE scenario_id = ? ORDER BY row, col",
                (SCN,),
            ).fetchall()
        ),
        json.dumps(
            c.execute(
                "SELECT * FROM constraints WHERE scenario_id = ? ORDER BY kind",
                (SCN,),
            ).fetchall()
        ),
        json.dumps(
            c.execute(
                "SELECT * FROM rules WHERE scenario_id = ? ORDER BY rule_id",
                (SCN,),
            ).fetchall()
        ),
        json.dumps(c.execute("SELECT * FROM scenarios WHERE id = ?", (SCN,)).fetchall()),
    ]
    c.close()
    return hashlib.sha256("".join(chunks).encode()).hexdigest()


class TestMilestone1:
    def test_m1_catalog_tables(self):
        """Bootstrap creates meta, chambers, components, constraints, rules, scenarios, sessions."""
        assert _init().returncode == 0
        c = _conn()
        names = {
            r[0]
            for r in c.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        }
        c.close()
        for want in (
            "meta",
            "chambers",
            "components",
            "constraints",
            "rules",
            "scenarios",
            "sessions",
        ):
            assert want in names

    def test_m1_alpha_nine_slots(self):
        """SCN-Alpha catalog holds nine chamber slots."""
        _init()
        c = _conn()
        n = c.execute("SELECT COUNT(*) FROM chambers WHERE scenario_id = ?", (SCN,)).fetchone()[0]
        c.close()
        assert n == 9

    def test_m1_limit_rows_three(self):
        """Three per-kind limit rows load for SCN-Alpha."""
        _init()
        c = _conn()
        n = c.execute("SELECT COUNT(*) FROM constraints WHERE scenario_id = ?", (SCN,)).fetchone()[0]
        kinds = {
            r[0]
            for r in c.execute(
                "SELECT kind FROM constraints WHERE scenario_id = ? ORDER BY kind", (SCN,)
            ).fetchall()
        }
        c.close()
        assert n == 3
        assert kinds == {"pump", "rod", "vent"}

    def test_m1_open_triple_seed(self):
        """Opening metric triple matches SCN-Alpha seed TOML."""
        _init()
        proc = subprocess.run(
            [FLUX, "status", "--json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert proc.returncode == 0
        doc = json.loads(proc.stdout)
        assert (doc["metric_a"], doc["metric_b"], doc["metric_c"]) == OPEN

    def test_m1_version_marker_two(self):
        """Schema version marker is 2 per bench precedence."""
        _init()
        proc = subprocess.run([FLUX, "status", "--json"], capture_output=True, text=True, timeout=15)
        doc = json.loads(proc.stdout)
        assert doc["schema_version"] == 2

    def test_m1_repeat_init_idempotent(self):
        """Repeat init yields identical catalog fingerprint."""
        _init()
        first = _catalog_fingerprint()
        subprocess.run([FLUX, "init", "--scenario", SCN], check=True, timeout=30)
        second = _catalog_fingerprint()
        assert first == second

    def test_m1_levels_nonzero(self):
        """Component levels match seed TOML rather than row indices."""
        _init()
        c = _conn()
        for (row, col), want in EXPECTED_LEVELS.items():
            got = c.execute(
                "SELECT level FROM components WHERE scenario_id = ? AND row = ? AND col = ?",
                (SCN, row, col),
            ).fetchone()[0]
            assert got == want, f"cell ({row},{col}) level {got} != {want}"
        c.close()

    def test_m1_catalog_fingerprint(self):
        """Catalog fingerprint is stable across reruns."""
        _init()
        first = _catalog_fingerprint()
        subprocess.run([FLUX, "init", "--scenario", SCN], check=True, timeout=30)
        second = _catalog_fingerprint()
        assert len(first) == 64
        assert first == second

    def test_m1_rule_priority_catalog(self):
        """Rules load in ascending priority with expected gate kinds and params."""
        _init()
        c = _conn()
        rows = c.execute(
            """
            SELECT rule_id, priority, rule_type, param_a
            FROM rules WHERE scenario_id = ?
            ORDER BY priority ASC
            """,
            (SCN,),
        ).fetchall()
        c.close()
        assert rows == [
            ("adj_same", 10, "adjacency_delta", 1),
            ("corner_cap", 20, "corner_cap", 2),
            ("type_max", 30, "type_max", 0),
        ]
        c = _conn()
        loss_a, band_a_hi, stable = c.execute(
            """
            SELECT loss_a, band_a_hi, stable_needed
            FROM scenarios WHERE id = ?
            """,
            (SCN,),
        ).fetchone()
        c.close()
        assert loss_a == 100
        assert band_a_hi == 60
        assert stable == 3
