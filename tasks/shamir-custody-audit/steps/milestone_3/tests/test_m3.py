"""Milestone 3 — Policy enforcement and fingerprint correctness."""

import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

BINARY = "/app/bin/audit"
DB = "/app/data/ceremonies.db"
DOSSIER = "/app/docs/ceremony-policy-v3.md"
REPORT = "/app/output/report.json"


# ─── GF(2^8) helpers (same field spec as Go implementation) ─────────────────

def _gf_mul(a: int, b: int) -> int:
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
    result = 0
    for i, (xi, yi) in enumerate(shares):
        num = den = 1
        for j, (xj, _) in enumerate(shares):
            if i != j:
                num = _gf_mul(num, xj)
                den = _gf_mul(den, xi ^ xj)
        result ^= _gf_mul(yi, _gf_mul(num, _gf_inv(den)))
    return result


def _reconstruct_from_db(session_id: str) -> bytes:
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
        col = [(x, int(y_hex[byte_idx * 2: byte_idx * 2 + 2], 16)) for x, y_hex in rows]
        secret[byte_idx] = _lagrange_zero(col)
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


class TestMilestone3:
    def test_m3_alpha_no_violations(self):
        """sess-alpha (primary/secondary/backup tiers) has no policy violations."""
        _run_audit()
        by_sess = _by_session(_load_report())
        assert by_sess["sess-alpha"]["policy_violations"] == [], (
            f"sess-alpha must have no violations; got {by_sess['sess-alpha']['policy_violations']}"
        )

    def test_m3_alpha_quorum_valid(self):
        """sess-alpha quorum_valid is true (no conflicting tiers)."""
        _run_audit()
        by_sess = _by_session(_load_report())
        assert by_sess["sess-alpha"]["quorum_valid"] is True

    def test_m3_gamma_has_violation(self):
        """sess-gamma (executive + auditor) reports cannot_coexist violation."""
        _run_audit()
        by_sess = _by_session(_load_report())
        violations = by_sess["sess-gamma"]["policy_violations"]
        assert len(violations) > 0, "sess-gamma must have at least one policy violation"
        assert any("cannot_coexist" in v for v in violations), (
            f"Expected cannot_coexist violation in {violations}"
        )

    def test_m3_gamma_quorum_invalid(self):
        """sess-gamma quorum_valid is false due to tier conflict."""
        _run_audit()
        by_sess = _by_session(_load_report())
        assert by_sess["sess-gamma"]["quorum_valid"] is False

    def test_m3_delta_no_violations(self):
        """sess-delta (executive only, no auditor) must NOT trigger cannot_coexist."""
        _run_audit()
        by_sess = _by_session(_load_report())
        violations = by_sess["sess-delta"]["policy_violations"]
        assert violations == [], (
            f"sess-delta has only executive tier, no auditor — "
            f"cannot_coexist requires BOTH tiers; got violations: {violations}"
        )

    def test_m3_delta_quorum_valid(self):
        """sess-delta quorum_valid is true (executive present but auditor absent)."""
        _run_audit()
        by_sess = _by_session(_load_report())
        assert by_sess["sess-delta"]["quorum_valid"] is True, (
            "sess-delta has only one tier of the constrained pair — must be valid"
        )

    def test_m3_fingerprint_length_16(self):
        """All non-null fingerprints are exactly 16 lowercase hex characters."""
        _run_audit()
        report = _load_report()
        for entry in report["audit_results"]:
            fp = entry["secret_fingerprint"]
            if fp is None:
                continue
            assert len(fp) == 16, (
                f"Session {entry['session_id']}: fingerprint length {len(fp)} != 16"
            )
            assert fp == fp.lower(), f"Fingerprint {fp!r} contains uppercase characters"
            assert all(c in "0123456789abcdef" for c in fp), (
                f"Fingerprint {fp!r} contains non-hex characters"
            )

    def test_m3_alpha_fingerprint_sha256(self):
        """sess-alpha fingerprint matches SHA-256 of correctly reconstructed secret."""
        _run_audit()
        by_sess = _by_session(_load_report())

        secret = _reconstruct_from_db("sess-alpha")
        assert secret, "Python reconstruction must succeed for sess-alpha"

        expected_fp = hashlib.sha256(secret).hexdigest()[:16]
        got_fp = by_sess["sess-alpha"]["secret_fingerprint"]
        assert got_fp == expected_fp, (
            f"sess-alpha fingerprint {got_fp!r} != expected SHA-256[:16] {expected_fp!r}; "
            f"check that SHA-256 (not SHA-1) is used and that 16 characters are taken"
        )

    def test_m3_delta_fingerprint_sha256(self):
        """sess-delta fingerprint matches SHA-256 of correctly reconstructed secret."""
        _run_audit()
        by_sess = _by_session(_load_report())

        secret = _reconstruct_from_db("sess-delta")
        assert secret, "Python reconstruction must succeed for sess-delta"

        expected_fp = hashlib.sha256(secret).hexdigest()[:16]
        got_fp = by_sess["sess-delta"]["secret_fingerprint"]
        assert got_fp == expected_fp, (
            f"sess-delta fingerprint {got_fp!r} != expected SHA-256[:16] {expected_fp!r}"
        )

    def test_m3_alpha_verification_verified(self):
        """sess-alpha verification_status is 'verified'."""
        _run_audit()
        by_sess = _by_session(_load_report())
        assert by_sess["sess-alpha"]["verification_status"] == "verified"

    def test_m3_gamma_verification_policy_violation(self):
        """sess-gamma verification_status is 'policy_violation'."""
        _run_audit()
        by_sess = _by_session(_load_report())
        assert by_sess["sess-gamma"]["verification_status"] == "policy_violation"

    def test_m3_beta_verification_failed(self):
        """sess-beta verification_status is 'failed' (insufficient shares)."""
        _run_audit()
        by_sess = _by_session(_load_report())
        assert by_sess["sess-beta"]["verification_status"] == "failed"

    def test_m3_delta_verification_verified(self):
        """sess-delta (executive only, valid) verification_status is 'verified'."""
        _run_audit()
        by_sess = _by_session(_load_report())
        assert by_sess["sess-delta"]["verification_status"] == "verified"

    def test_m3_fingerprint_does_not_match_any_sha1_variant(self):
        """Fingerprints must use SHA-256, not SHA-1 in any form (raw or base64-encoded input).

        The buggy implementation computes SHA-1(base64(secret))[:8].  There are two
        plausible SHA-1 variants to rule out:
          1. SHA-1(raw_secret)[:N]        — SHA-1 on raw bytes, any truncation
          2. SHA-1(base64(secret))[:N]    — SHA-1 on base64 encoding, any truncation

        Both must be rejected for every session that produces a fingerprint.
        Only SHA-256(raw_secret)[:16] is acceptable.
        """
        _run_audit()
        report = _load_report()

        for entry in report["audit_results"]:
            fp = entry["secret_fingerprint"]
            if fp is None:
                continue
            sid = entry["session_id"]
            secret = _reconstruct_from_db(sid)
            if not secret:
                continue

            # SHA-1 over raw bytes — various truncation lengths
            sha1_raw = hashlib.sha1(secret).hexdigest()  # noqa: S324
            assert not sha1_raw.startswith(fp), (
                f"{sid}: fingerprint {fp!r} matches a prefix of SHA-1(raw_secret)={sha1_raw!r}; "
                "use SHA-256, not SHA-1"
            )

            # SHA-1 over base64-encoded bytes — the specific intermediate-state variant
            import base64 as _b64
            sha1_b64 = hashlib.sha1(_b64.b64encode(secret)).hexdigest()  # noqa: S324
            assert not sha1_b64.startswith(fp), (
                f"{sid}: fingerprint {fp!r} matches SHA-1(base64(secret))[:8]={sha1_b64[:8]!r}; "
                "the M3 fix must replace SHA-1+base64 with SHA-256 on raw bytes"
            )

    def test_m3_violation_count_matches_active_constraint_pairs(self):
        """policy_violations length equals the number of cannot_coexist pairs where
        BOTH constrained tiers are simultaneously present in the session's slot_registry.

        The buggy implementation uses OR (||) instead of AND (&&), so it fires when
        EITHER tier is present.  For sess-delta (only 'executive', no 'auditor') the bug
        incorrectly reports 1 violation; the corrected AND logic reports 0.
        """
        _run_audit()
        by_sess = _by_session(_load_report())

        conn = sqlite3.connect(DB)
        for sid in ("sess-alpha", "sess-gamma", "sess-delta"):
            # Count constraint pairs where both tier_alpha AND tier_beta are present.
            active = conn.execute(
                """
                SELECT COUNT(DISTINCT tc.constraint_id)
                FROM tier_constraints tc
                WHERE tc.rule_kind = 'cannot_coexist'
                  AND EXISTS (
                      SELECT 1 FROM slot_registry sr
                      WHERE sr.session_id = ? AND sr.auth_tier = tc.tier_alpha
                  )
                  AND EXISTS (
                      SELECT 1 FROM slot_registry sr
                      WHERE sr.session_id = ? AND sr.auth_tier = tc.tier_beta
                  )
                """,
                (sid, sid),
            ).fetchone()[0]

            reported = len(by_sess[sid]["policy_violations"])
            assert reported == active, (
                f"{sid}: tool reports {reported} violation(s) but "
                f"{active} constraint pair(s) have both tiers present; "
                "cannot_coexist requires BOTH tiers — check that && (AND) is used, not || (OR)"
            )
        conn.close()
