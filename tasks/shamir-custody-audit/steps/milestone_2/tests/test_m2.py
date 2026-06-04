"""Milestone 2 — Shamir secret reconstruction correctness."""

import base64
import hashlib  # noqa: S324
import json
import sqlite3
import subprocess
from pathlib import Path

BINARY = "/app/bin/audit"
DB = "/app/data/ceremonies.db"
DOSSIER = "/app/docs/ceremony-policy-v3.md"
REPORT = "/app/output/report.json"


# ─── GF(2^8) helpers (same field as the Go implementation) ──────────────────

def _gf_mul(a: int, b: int) -> int:
    """Multiply two GF(2^8) elements; irreducible poly 0x11b."""
    p = 0
    while b:
        if b & 1:
            p ^= a
        carry = a & 0x80
        a = (a << 1) & 0xFF
        if carry:
            a ^= 0x1B
        b >>= 1
    return p


def _gf_inv(a: int) -> int:
    """Multiplicative inverse via Fermat: a^254 in GF(2^8)."""
    if a == 0:
        return 0
    result, base, exp = 1, a, 254
    while exp:
        if exp & 1:
            result = _gf_mul(result, base)
        base = _gf_mul(base, base)
        exp >>= 1
    return result


def _lagrange_zero(shares: list[tuple[int, int]]) -> int:
    """Lagrange interpolation at x=0 for one byte column."""
    result = 0
    for i, (xi, yi) in enumerate(shares):
        num = den = 1
        for j, (xj, _) in enumerate(shares):
            if i != j:
                num = _gf_mul(num, xj)
                den = _gf_mul(den, xi ^ xj)
        li = _gf_mul(num, _gf_inv(den))
        result ^= _gf_mul(yi, li)
    return result


def _reconstruct_from_db(session_id: str) -> bytes:
    """Read shares from DB and reconstruct the secret using Python Lagrange."""
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        """
        SELECT ss.coord_x, ss.coord_y_hex
        FROM share_submissions ss
        JOIN slot_registry sr ON sr.slot_id = ss.slot_id
        WHERE sr.session_id = ?
        ORDER BY ss.coord_x
        """,
        (session_id,),
    ).fetchall()
    threshold = conn.execute(
        "SELECT threshold_k FROM sessions WHERE session_id = ?", (session_id,)
    ).fetchone()[0]
    conn.close()

    if len(rows) < threshold:
        return b""

    byte_len = len(rows[0][1]) // 2
    secret = bytearray(byte_len)
    for byte_idx in range(byte_len):
        share_col = [(x, int(y_hex[byte_idx * 2: byte_idx * 2 + 2], 16)) for x, y_hex in rows]
        secret[byte_idx] = _lagrange_zero(share_col)
    return bytes(secret)


def _run_audit() -> None:
    proc = subprocess.run(
        [BINARY, "--db", DB, "--dossier", DOSSIER, "--out", REPORT],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, f"audit failed: {proc.stderr}"


def _load_report() -> dict:
    return json.loads(Path(REPORT).read_text())


def _by_session(report: dict) -> dict:
    return {e["session_id"]: e for e in report["audit_results"]}


class TestMilestone2:
    def test_m2_alpha_reconstruction_success(self):
        """sess-alpha (3 shares, threshold=3) reconstructs successfully."""
        _run_audit()
        by_sess = _by_session(_load_report())
        assert by_sess["sess-alpha"]["reconstruction_status"] == "success"

    def test_m2_beta_insufficient_shares(self):
        """sess-beta (2 shares, threshold=3) reports insufficient_shares."""
        _run_audit()
        by_sess = _by_session(_load_report())
        assert by_sess["sess-beta"]["reconstruction_status"] == "insufficient_shares"

    def test_m2_gamma_reconstruction_success(self):
        """sess-gamma (3 shares, threshold=3) reconstructs despite policy violation."""
        _run_audit()
        by_sess = _by_session(_load_report())
        assert by_sess["sess-gamma"]["reconstruction_status"] == "success"

    def test_m2_delta_reconstruction_success(self):
        """sess-delta (2 shares, threshold=2) reconstructs successfully."""
        _run_audit()
        by_sess = _by_session(_load_report())
        assert by_sess["sess-delta"]["reconstruction_status"] == "success"

    def test_m2_threshold_met_flags(self):
        """threshold_met is true for sessions with enough shares, false otherwise."""
        _run_audit()
        by_sess = _by_session(_load_report())
        assert by_sess["sess-alpha"]["threshold_met"] is True
        assert by_sess["sess-beta"]["threshold_met"] is False
        assert by_sess["sess-gamma"]["threshold_met"] is True
        assert by_sess["sess-delta"]["threshold_met"] is True

    def test_m2_beta_fingerprint_null(self):
        """sess-beta fingerprint is null when reconstruction fails."""
        _run_audit()
        by_sess = _by_session(_load_report())
        assert by_sess["sess-beta"]["secret_fingerprint"] is None

    def test_m2_alpha_fingerprint_matches_independent_reconstruction(self):
        """sess-alpha fingerprint is SHA-1(base64(correct_secret))[:8] after M2 fix."""
        _run_audit()
        by_sess = _by_session(_load_report())

        correct_secret = _reconstruct_from_db("sess-alpha")
        assert correct_secret, "Python reconstruction returned empty bytes"
        assert len(correct_secret) == 8, f"Expected 8-byte secret, got {len(correct_secret)}"

        # The code uses SHA-1(base64(secret))[:8] as fingerprint (M3 fixes this).
        # This test verifies that the secret is correctly reconstructed at x=0.
        expected_fp = hashlib.sha1(base64.b64encode(correct_secret)).hexdigest()[:8]  # noqa: S324
        got_fp = by_sess["sess-alpha"]["secret_fingerprint"]
        assert got_fp == expected_fp, (
            f"Fingerprint {got_fp!r} does not match SHA-1(base64(correct_secret))={expected_fp!r}; "
            "reconstruction may be evaluating at the wrong field coordinate"
        )

    def test_m2_delta_fingerprint_matches_independent_reconstruction(self):
        """sess-delta fingerprint is SHA-1(base64(correct_secret))[:8] after M2 fix."""
        _run_audit()
        by_sess = _by_session(_load_report())

        correct_secret = _reconstruct_from_db("sess-delta")
        assert correct_secret, "Python reconstruction returned empty bytes"
        assert len(correct_secret) == 8

        expected_fp = hashlib.sha1(base64.b64encode(correct_secret)).hexdigest()[:8]  # noqa: S324
        got_fp = by_sess["sess-delta"]["secret_fingerprint"]
        assert got_fp == expected_fp, (
            f"Fingerprint {got_fp!r} does not match SHA-1(base64(correct_secret))={expected_fp!r}; "
            "reconstruction may be evaluating at the wrong field coordinate"
        )

    def test_m2_gamma_intermediate_fingerprint_correct(self):
        """sess-gamma fingerprint is SHA-1(base64(correct_secret))[:8] — reconstruction
        must succeed even though policy violations exist in sess-gamma.

        Gamma secret is b'abcdefgh' (0x61-0x68).  Shares are at x=1,2,3 with a
        degree-2 polynomial over GF(2^8).  Evaluating at x=1 (the M2 bug) returns
        the share at x=1 (0x6360...), not the constant term.
        """
        _run_audit()
        by_sess = _by_session(_load_report())

        correct_secret = _reconstruct_from_db("sess-gamma")
        assert correct_secret, "Python reconstruction returned empty for sess-gamma"
        assert len(correct_secret) == 8, f"Expected 8-byte secret, got {len(correct_secret)}"

        expected_fp = hashlib.sha1(base64.b64encode(correct_secret)).hexdigest()[:8]  # noqa: S324
        got_fp = by_sess["sess-gamma"]["secret_fingerprint"]
        assert got_fp == expected_fp, (
            f"sess-gamma fingerprint {got_fp!r} != SHA-1(base64(correct))={expected_fp!r}; "
            "reconstruction may be evaluated at x=1 instead of x=0 — "
            "note: a policy violation does NOT suppress reconstruction"
        )

    def test_m2_delta_degree1_closed_form_matches_fingerprint(self):
        """sess-delta uses a degree-1 polynomial; verify via the analytic closed form.

        For f(x) = s XOR gfMul(a, x) with two known points (x1,y1) and (x2,y2):
            slope a = gfMul(y1 XOR y2, gfInv(x1 XOR x2))
            secret s = y1 XOR gfMul(a, x1)

        This computes f(0) without any Lagrange summation loop, exercising a
        completely independent code path.  If the tool evaluates at x=1 (the M2 bug),
        the fingerprint will match SHA-1(base64(f(1))) instead of SHA-1(base64(f(0))).
        """
        _run_audit()
        by_sess = _by_session(_load_report())

        conn = sqlite3.connect(DB)
        rows = conn.execute(
            """
            SELECT ss.coord_x, ss.coord_y_hex
            FROM share_submissions ss
            JOIN slot_registry sr ON sr.slot_id = ss.slot_id
            WHERE sr.session_id = 'sess-delta'
            ORDER BY ss.coord_x
            """,
        ).fetchall()
        conn.close()

        assert len(rows) == 2, f"Expected 2 shares for sess-delta, got {len(rows)}"
        x1, y1_hex = rows[0]
        x2, y2_hex = rows[1]
        y1 = bytes.fromhex(y1_hex)
        y2 = bytes.fromhex(y2_hex)

        # Closed-form: slope per byte, then constant term per byte
        byte_len = len(y1)
        secret = bytearray(byte_len)
        inv_x_diff = _gf_inv(x1 ^ x2)
        for i in range(byte_len):
            slope = _gf_mul(y1[i] ^ y2[i], inv_x_diff)
            secret[i] = y1[i] ^ _gf_mul(slope, x1)
        secret_bytes = bytes(secret)

        expected_fp = hashlib.sha1(base64.b64encode(secret_bytes)).hexdigest()[:8]  # noqa: S324
        got_fp = by_sess["sess-delta"]["secret_fingerprint"]
        assert got_fp == expected_fp, (
            f"sess-delta fingerprint {got_fp!r} != closed-form SHA-1(base64(f(0)))={expected_fp!r}; "
            f"closed-form secret={secret_bytes.hex()!r}; "
            "if the tool returns the share value at x=1 instead of the constant term, "
            "the fingerprint will differ"
        )
