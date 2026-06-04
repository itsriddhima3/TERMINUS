"""Milestone 2 — bearer access report (strict local/API/crypto parity)."""

import base64
import hashlib
import json
import pathlib
import sqlite3
import subprocess
import time
import urllib.request

import pytest

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

REPORT = pathlib.Path("/app/output/access_report.json")
RUNTIME = pathlib.Path("/app/platform/runtime.json")

NEGATIVE_CASES = frozenset(
    {
        "expired_token",
        "tampered_sig",
        "unknown_kid",
        "alg_header_mismatch",
        "future_nbf",
        "issuer_drift",
        "stripped_signature",
    }
)


def _load_report() -> dict:
    assert REPORT.exists(), f"missing {REPORT}"
    with REPORT.open(encoding="utf-8") as fh:
        data = json.load(fh)
    assert isinstance(data, dict)
    return data


def _case_row(data: dict, case_id: str) -> dict:
    rows = [r for r in data["checks"] if r["case_id"] == case_id]
    assert len(rows) == 1, f"expected one row for {case_id}"
    return rows[0]


def _active_kid_db() -> str:
    conn = sqlite3.connect("/app/var/vault.db")
    try:
        row = conn.execute(
            "SELECT kid FROM signing_keys WHERE status = 'active' LIMIT 1"
        ).fetchone()
        assert row is not None
        return str(row[0])
    finally:
        conn.close()


def _pub_pem_for_kid(kid: str) -> str:
    conn = sqlite3.connect("/app/var/vault.db")
    try:
        row = conn.execute(
            "SELECT public_pem FROM signing_keys WHERE kid = ?",
            (kid,),
        ).fetchone()
        assert row is not None
        return str(row[0])
    finally:
        conn.close()


def _b64url_decode(segment: str) -> bytes:
    pad = "=" * ((4 - len(segment) % 4) % 4)
    return base64.urlsafe_b64decode(segment + pad)


def _jwt_parts(token: str) -> tuple[dict, dict, bytes]:
    parts = token.split(".")
    assert len(parts) == 3
    header = json.loads(_b64url_decode(parts[0]))
    payload = json.loads(_b64url_decode(parts[1]))
    sig = _b64url_decode(parts[2]) if parts[2] else b""
    return header, payload, sig


def _independent_crypto_ok(token: str) -> bool:
    try:
        header, payload, sig = _jwt_parts(token)
    except Exception:
        return False
    if not sig or header.get("alg") != "RS256":
        return False
    kid = header.get("kid", "")
    try:
        pem = _pub_pem_for_kid(kid)
    except AssertionError:
        return False
    pub = serialization.load_pem_public_key(pem.encode())
    data = (token.split(".")[0] + "." + token.split(".")[1]).encode()
    pub.verify(sig, data, padding.PKCS1v15(), hashes.SHA256())
    now = int(time.time())
    if payload.get("iss") != "vault-edge":
        return False
    if int(payload.get("nbf", 0)) > now:
        return False
    if int(payload.get("exp", 0)) < now:
        return False
    return True


def _token_gate_result(token: str) -> dict:
    script = r"""
declare(strict_types=1);
require_once '/app/cli/src/Bootstrap.php';
require_once '/app/cli/src/JwtCrypto.php';
require_once '/app/cli/src/ClockSkew.php';
require_once '/app/cli/src/KeyMaterial.php';
require_once '/app/cli/src/SigLane.php';
require_once '/app/cli/src/EdgeVerifier.php';
require_once '/app/cli/src/TokenGate.php';

$token = trim(stream_get_contents(STDIN));
$gate = new \Vault\Cli\TokenGate(\Vault\Cli\Bootstrap::pdo());
echo json_encode($gate->op_verify_a($token), JSON_THROW_ON_ERROR);
"""
    result = subprocess.run(
        ["php", "-r", script],
        input=token.encode(),
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr.decode()
    data = json.loads(result.stdout.decode())
    assert isinstance(data, dict)
    return data


def _tamper_subject(token: str) -> str:
    parts = token.split(".")
    payload = json.loads(_b64url_decode(parts[1]))
    payload["sub"] = "intruder"
    parts[1] = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()
    return ".".join(parts)


def _matrix_digest(checks: list[dict]) -> str:
    tuples = [
        [r["case_id"], r["accepted"], r["local_ok"], r["api_ok"], r["crypto_ok"], r["http_status"]]
        for r in checks
    ]
    return hashlib.sha256(json.dumps(tuples, separators=(",", ":")).encode()).hexdigest()


@pytest.fixture(autouse=True, scope="session")
def ensure_api_running():
    subprocess.run(
        ["bash", "/app/scripts/start-api.sh"],
        check=True,
        timeout=15,
    )


def _fresh_login_token() -> str:
    rt = json.loads(RUNTIME.read_text(encoding="utf-8"))
    payload = json.dumps(
        {"username": rt["login_user"], "password": rt["login_password"]}
    ).encode()
    req = urllib.request.Request(
        f"{rt['api_base']}/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        body = json.load(resp)
    return str(body["access_token"])


class TestMilestone2:
    def test_guardctl_verify_regenerates_access_report(self):
        """Verify guardctl verify runs and local verification passes."""
        if REPORT.exists():
            REPORT.unlink()
        result = subprocess.run(
            ["/app/cli/guardctl", "verify"],
            capture_output=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr.decode()
        assert REPORT.exists(), "guardctl verify did not produce output"
        row = _case_row(_load_report(), "valid_session")
        assert row["local_ok"] is True
        second = subprocess.run(
            ["/app/cli/guardctl", "verify"],
            capture_output=True,
            timeout=60,
        )
        assert second.returncode == 0, second.stderr.decode()
        rerun_row = _case_row(_load_report(), "valid_session")
        assert rerun_row["local_ok"] is True

    def test_report_top_level_contract(self):
        """Verify report top level contract."""
        data = _load_report()
        assert set(data.keys()) == {
            "checks",
            "all_pass",
            "fixture_order",
            "catalog_size",
            "matrix_digest",
        }
        rt = json.loads(RUNTIME.read_text(encoding="utf-8"))
        assert data["catalog_size"] == len(rt["fixture_cases"]) == 8

    def test_fixture_order_and_check_order(self):
        """Verify fixture order and check order."""
        data = _load_report()
        rt = json.loads(RUNTIME.read_text(encoding="utf-8"))
        assert data["fixture_order"] == rt["fixture_cases"]
        assert [r["case_id"] for r in data["checks"]] == data["fixture_order"]

    def test_matrix_digest_matches_checks(self):
        """Verify matrix digest matches checks."""
        data = _load_report()
        assert data["matrix_digest"] == _matrix_digest(data["checks"])

    def test_valid_session_full_acceptance(self):
        """Verify valid session full acceptance."""
        token = _fresh_login_token()
        _, payload, _ = _jwt_parts(token)
        row = _case_row(_load_report(), "valid_session")
        assert row["accepted"] is True
        assert row["local_ok"] is True
        assert row["api_ok"] is True
        assert row["crypto_ok"] is True
        assert row["http_status"] == 200
        assert row["alg_seen"] == "RS256"
        assert row["kid_seen"] == _active_kid_db()
        assert row["iss_seen"] == "vault-edge"
        assert row["nbf_seen"] == int(payload.get("nbf", 0))
        assert row["exp_seen"] == int(payload["exp"])
        assert row["subject"] == "operator"
        assert row["subject_matches"] is True

    def test_valid_session_independent_crypto_verify(self):
        """Verify valid session independent crypto verify."""
        token = _fresh_login_token()
        assert _independent_crypto_ok(token)
        row = _case_row(_load_report(), "valid_session")
        assert row["crypto_ok"] is True

    def test_token_gate_accepts_fresh_rsa_bearer_directly(self):
        """Verify TokenGate itself accepts fresh RSA bearers and rejects tampering."""
        token = _fresh_login_token()
        valid = _token_gate_result(token)
        assert valid["ok"] is True
        tampered = _token_gate_result(_tamper_subject(token))
        assert tampered["ok"] is False

    def test_negative_cases_fully_rejected(self):
        """Verify negative cases fully rejected."""
        data = _load_report()
        for case_id in NEGATIVE_CASES:
            row = _case_row(data, case_id)
            assert row["accepted"] is False
            assert row["local_ok"] is False
            assert row["api_ok"] is False
            assert row["crypto_ok"] is False
            assert row["http_status"] == 401

    def test_unknown_kid_foreign_kid(self):
        """Verify unknown kid foreign kid."""
        row = _case_row(_load_report(), "unknown_kid")
        assert row["kid_seen"] == "key-404"
        assert row["kid_seen"] != _active_kid_db()

    def test_alg_header_mismatch_hs256(self):
        """Verify alg header mismatch hs256."""
        row = _case_row(_load_report(), "alg_header_mismatch")
        assert row["alg_seen"] == "HS256"

    def test_future_nbf_claim_is_future(self):
        """Verify future nbf claim is future."""
        token = _fresh_login_token()
        parts = token.split(".")
        payload = json.loads(_b64url_decode(parts[1]))
        payload["nbf"] = int(time.time()) + 3600
        parts[1] = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(",", ":")).encode()
        ).rstrip(b"=").decode()
        crafted = ".".join(parts)
        _, crafted_payload, _ = _jwt_parts(crafted)
        row = _case_row(_load_report(), "future_nbf")
        expected_nbf = int(crafted_payload["nbf"])
        assert abs(row["nbf_seen"] - expected_nbf) <= 120
        assert row["nbf_seen"] > int(time.time()) + 3000

    def test_issuer_drift_claim(self):
        """Verify issuer drift claim."""
        row = _case_row(_load_report(), "issuer_drift")
        assert row["iss_seen"] == "rogue-issuer"

    def test_stripped_signature_empty_crypto(self):
        """Verify stripped signature empty crypto."""
        row = _case_row(_load_report(), "stripped_signature")
        assert row["crypto_ok"] is False

    def test_each_row_has_full_field_set(self):
        """Verify each row has full field set."""
        base = {
            "case_id",
            "accepted",
            "local_ok",
            "api_ok",
            "crypto_ok",
            "http_status",
            "kid_seen",
            "alg_seen",
            "iss_seen",
            "nbf_seen",
            "exp_seen",
        }
        data = _load_report()
        for row in data["checks"]:
            assert base.issubset(row.keys())
            if row["case_id"] == "valid_session":
                assert {"subject", "subject_matches"}.issubset(row.keys())

    def test_all_pass_requires_clean_matrix(self):
        """Verify all pass requires clean matrix."""
        data = _load_report()
        assert data["all_pass"] is True
        for case_id in NEGATIVE_CASES:
            row = _case_row(data, case_id)
            assert not (row["accepted"] or row["local_ok"] or row["api_ok"] or row["crypto_ok"])

    def test_checks_cover_exact_catalog(self):
        """Verify checks cover exact catalog."""
        data = _load_report()
        rt = json.loads(RUNTIME.read_text(encoding="utf-8"))
        assert {r["case_id"] for r in data["checks"]} == set(rt["fixture_cases"])
