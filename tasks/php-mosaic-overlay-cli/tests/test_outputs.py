"""Verifier for php-mosaic-overlay-cli.

Each test below scripts the CLI over stdin under a deterministic scripted
clock and asserts post-conditions on the sqlite database. Expected values
are computed from the scoring profile + fixture geometry, not hard-coded
magic numbers from the instruction.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path

APP_ROOT = Path("/app")
DB_PATH = APP_ROOT / "state" / "challenges.db"
CLI = ["php", str(APP_ROOT / "cli" / "overlay-inspect")]


def _profile() -> dict:
    return json.loads((APP_ROOT / "config" / "scoring_profile.json").read_text())


def _grid() -> dict:
    return json.loads((APP_ROOT / "config" / "grid_dimensions.json").read_text())


def _challenge_meta(cid: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM challenges WHERE challenge_id = ?", (cid,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def _region_id_for(cid: str, label_substring: str) -> str:
    """Resolve the seeded region id for a challenge by a label substring.

    Lookups go through the seed data so the tests do not hard-code the
    particular id strings the seed happens to use.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT region_id, region_label FROM region_defs "
            "WHERE challenge_id = ?",
            (cid,),
        ).fetchall()
        for r in rows:
            if label_substring in r["region_label"]:
                return r["region_id"]
        raise AssertionError(
            f"no seeded region with label containing {label_substring!r}"
            f" for challenge {cid}; available={[dict(r) for r in rows]}"
        )
    finally:
        conn.close()


def _region_ids_for(cid: str) -> set[str]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT region_id FROM region_defs WHERE challenge_id = ?", (cid,)
        ).fetchall()
        return {r["region_id"] for r in rows}
    finally:
        conn.close()


def _run(args: list[str], stdin: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["SCRIPTED_CLOCK"] = "1"
    return subprocess.run(
        CLI + args,
        input=stdin,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )


def _reset() -> None:
    proc = subprocess.run(CLI + ["reset"], capture_output=True, text=True, timeout=15)
    assert proc.returncode == 0, proc.stderr


def _play(cid: str, stdin_lines: list[str], resume_session: int | None = None) -> subprocess.CompletedProcess[str]:
    args = ["play", cid]
    if resume_session is not None:
        args.append(str(resume_session))
    text = "\n".join(stdin_lines) + "\n"
    proc = _run(args, text)
    assert proc.returncode == 0, (
        f"play failed: rc={proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    return proc


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _latest_session(cid: str) -> int:
    with _conn() as c:
        row = c.execute(
            "SELECT MAX(session_row_id) AS s FROM sessions WHERE challenge_id = ?",
            (cid,),
        ).fetchone()
        return int(row["s"])


def _hints(session_id: int) -> list[sqlite3.Row]:
    with _conn() as c:
        return list(c.execute(
            "SELECT * FROM hints WHERE session_row_id = ? ORDER BY sequence_no",
            (session_id,),
        ).fetchall())


def _marks(session_id: int) -> list[sqlite3.Row]:
    with _conn() as c:
        return list(c.execute(
            "SELECT * FROM marks WHERE session_row_id = ? ORDER BY sequence_no",
            (session_id,),
        ).fetchall())


def _session(session_id: int) -> sqlite3.Row:
    with _conn() as c:
        return c.execute(
            "SELECT * FROM sessions WHERE session_row_id = ?",
            (session_id,),
        ).fetchone()


# ---------------------------------------------------------------------------
# Topology A: rendered-cell to source-pixel projection + polygon classification
# ---------------------------------------------------------------------------

class TestProjectionAndClassification:
    """Marks placed near the bottom edge of the rendered preview should
    correctly resolve against polygon regions stored in source pixel space.
    """

    def setup_method(self):
        _reset()

    def test_inner_pixel_recorded_when_input_inside_polygon(self):
        """Mid-polygon mark resolves to a hit on the expected region."""
        expected = _region_id_for("ch_alpha", "lower_left")
        _play("ch_alpha", ["tick 1000", "mark 6 15", "quit"])
        marks = _marks(_latest_session("ch_alpha"))
        assert len(marks) == 1
        assert int(marks[0]["matched"]) == 1, dict(marks[0])
        assert marks[0]["matched_region_id"] == expected

    def test_corner_pixel_classified_against_polygon(self):
        """Mark placed near the polygon's upper-right corner resolves to a hit."""
        expected = _region_id_for("ch_alpha", "lower_left")
        _play("ch_alpha", ["tick 1000", "mark 14 18", "quit"])
        marks = _marks(_latest_session("ch_alpha"))
        assert len(marks) == 1
        assert int(marks[0]["matched"]) == 1, dict(marks[0])
        assert marks[0]["matched_region_id"] == expected

    def test_outer_pixel_yields_no_hit(self):
        """A rendered cell whose inverse projection lies outside the source
        frame must register as a miss, even when the polygon happens to lie
        in the same axis range as the wrongly-folded coordinate.
        """
        _play("ch_alpha", ["tick 1000", "mark 6 30", "quit"])
        marks = _marks(_latest_session("ch_alpha"))
        assert len(marks) == 1
        assert int(marks[0]["matched"]) == 0, dict(marks[0])
        assert marks[0]["matched_region_id"] in (None, "")


# ---------------------------------------------------------------------------
# Topology B: session lifecycle across pause/resume
# ---------------------------------------------------------------------------

class TestLifecycleAcrossPauseResume:
    def setup_method(self):
        _reset()

    def test_first_pull_after_resume_not_double_charged(self):
        """One hint command before pause and one after resume should produce
        exactly two hint rows in the database for that session."""
        _play("ch_alpha", ["tick 1000", "hint", "pause"])
        sid = _latest_session("ch_alpha")
        _play("ch_alpha", ["tick 1000", "hint", "quit"], resume_session=sid)
        rows = _hints(sid)
        assert len(rows) == 2, [dict(r) for r in rows]

    def test_tally_intact_across_pause_resume(self):
        """Three hint commands across a pause boundary must yield exactly
        three hint rows on the session."""
        _play("ch_alpha", ["tick 1000", "hint", "tick 1000", "hint", "pause"])
        sid = _latest_session("ch_alpha")
        _play("ch_alpha", ["tick 1000", "hint", "quit"], resume_session=sid)
        rows = _hints(sid)
        assert len(rows) == 3, [dict(r) for r in rows]

    def test_resumed_total_matches_continuous_total(self):
        """The continuous and paused-then-resumed plays of the same scripted
        sequence must close with identical final scores."""
        # Continuous trace.
        _reset()
        _play("ch_alpha", ["tick 1000", "hint", "tick 1000", "hint", "quit"])
        cont_sid = _latest_session("ch_alpha")
        cont_score = int(_session(cont_sid)["score"])

        # Resumed trace.
        _reset()
        _play("ch_alpha", ["tick 1000", "hint", "pause"])
        sid = _latest_session("ch_alpha")
        _play("ch_alpha", ["tick 1000", "hint", "quit"], resume_session=sid)
        res_score = int(_session(sid)["score"])

        assert cont_score == res_score, (cont_score, res_score)


# ---------------------------------------------------------------------------
# Topology C: rate-bucket admission + final-value composer
# ---------------------------------------------------------------------------

class TestRateBucketAndComposer:
    def setup_method(self):
        _reset()

    def test_throttle_bucket_does_not_absolve_second_pull(self):
        """A second hint inside an active bucket must incur the per-draw
        penalty configured in the scoring profile."""
        prof = _profile()
        _play("ch_alpha", ["tick 1000", "hint", "tick 1000", "hint", "quit"])
        sid = _latest_session("ch_alpha")
        rows = _hints(sid)
        assert len(rows) == 2
        assert int(rows[0]["incurred_penalty"]) == 0
        assert int(rows[1]["incurred_penalty"]) == int(prof["penalty_per_hint"])

    def test_extra_pull_never_yields_higher_total(self):
        """A trace with an additional hint inside the same bucket may not
        produce a strictly higher score than the baseline trace."""
        _reset()
        _play("ch_alpha", ["tick 1000", "hint", "quit"])
        baseline = int(_session(_latest_session("ch_alpha"))["score"])

        _reset()
        _play("ch_alpha", ["tick 1000", "hint", "tick 1000", "hint", "quit"])
        extra = int(_session(_latest_session("ch_alpha"))["score"])

        assert extra <= baseline, (baseline, extra)

    def test_total_rounded_after_penalty_composition(self):
        """The persisted score must be a multiple of the configured rounding
        step. This holds only when the final composition rounds after the
        bonus and penalty arithmetic, not before."""
        prof = _profile()
        step = int(prof["rounding_step"])
        _play("ch_alpha", ["mark 55 4", "quit"])
        sid = _latest_session("ch_alpha")
        score = int(_session(sid)["score"])
        assert score % step == 0, (score, step)
        # Computed expectation from the public scoring profile:
        #   base + 1 matched mark bonus + 1 hint reveal bonus * 0 hints
        #   - 0 penalties - 0 decay, snapped to rounding step.
        meta = _challenge_meta("ch_alpha")
        base = int(meta["base_units"])
        bonus = int(prof["bonus_per_match"])
        expected_pre = base + bonus
        # Banker-agnostic round-half-up for the integer profile values.
        q = (expected_pre + step // 2) // step
        expected = q * step
        assert score == expected, (score, expected)


# ---------------------------------------------------------------------------
# Integration: full play must round-trip through the persistence layer in
# agreement with the engine's authoritative action log.
# ---------------------------------------------------------------------------

class TestIntegration:
    def setup_method(self):
        _reset()

    def test_persisted_state_matches_authoritative_log_after_clean_pass(self):
        """End-to-end play exercising classification, lifecycle, and scoring
        produces database state consistent with a recomputed score."""
        prof = _profile()
        _play("ch_alpha", [
            "tick 1000",
            "mark 55 4",
            "tick 1000",
            "mark 6 15",
            "tick 1000",
            "hint",
            "pause",
        ])
        sid = _latest_session("ch_alpha")
        _play("ch_alpha", [
            "tick 1000",
            "hint",
            "tick 5000",
            "quit",
        ], resume_session=sid)

        marks = _marks(sid)
        hints = _hints(sid)
        sess = _session(sid)

        assert len(marks) == 2
        assert sum(int(m["matched"]) for m in marks) == 2
        expected_top = _region_id_for("ch_alpha", "upper_mid")
        expected_left = _region_id_for("ch_alpha", "lower_left")
        assert {m["matched_region_id"] for m in marks} == {
            expected_top,
            expected_left,
        }
        assert len(hints) == 2
        assert int(hints[0]["incurred_penalty"]) == 0
        assert int(hints[1]["incurred_penalty"]) == int(prof["penalty_per_hint"])

        meta = _challenge_meta("ch_alpha")
        base = int(meta["base_units"])
        decay = int(prof["decay_per_second"]) * int(sess["closed_at_ms"]) // 1000
        penalties = sum(int(h["incurred_penalty"]) for h in hints)
        matched_marks = sum(int(m["matched"]) for m in marks)
        bonus = (
            matched_marks * int(prof["bonus_per_match"])
            + len(hints) * int(prof["hint_reveal_bonus"])
        )
        pre = base - decay - penalties + bonus
        step = int(prof["rounding_step"])
        q = (pre + step // 2) // step
        expected = q * step
        assert int(sess["score"]) == expected, (sess["score"], expected)
        assert sess["closed_reason"] is not None and sess["closed_reason"] != ""
        assert sess["closed_at_ms"] is not None
