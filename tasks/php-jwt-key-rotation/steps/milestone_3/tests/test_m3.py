"""Milestone 3 — rotation audit, grace window, persistence, crypto cross-checks."""

import hashlib
import json
import pathlib
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

AUDIT = pathlib.Path("/app/output/rotation_audit.json")
DB = "/app/var/vault.db"
RUNTIME = pathlib.Path("/app/platform/runtime.json")
BOOTSTRAP_KEY = pathlib.Path("/app/data/bootstrap/key-001.pem")

REQUIRED = {
    "rotated",
    "previous_kid",
    "active_kid",
    "audit_rows",
    "verify_after_rotate",
    "pre_rotate_token_valid",
    "pre_rotate_kid",
    "post_rotate_kid",
    "previous_private_cleared",
    "jwks_kids",
    "previous_row_count",
    "audit_sequence_ok",
    "audit_chain_digest",
    "pre_crypto_ok",
    "post_crypto_ok",
    "signing_key_row_count",
}


def _load_audit() -> dict:
    assert AUDIT.exists(), f"missing {AUDIT}"
    with AUDIT.open(encoding="utf-8") as fh:
        data = json.load(fh)
    assert isinstance(data, dict)
    return data


def _db_rows(sql: str, params: tuple = ()) -> list[tuple]:
    conn = sqlite3.connect(DB)
    try:
        return list(conn.execute(sql, params))
    finally:
        conn.close()


def _audit_chain_digest() -> str:
    rows = _db_rows(
        "SELECT id, event_type, kid, detail_json, created_at FROM audit_log ORDER BY id ASC"
    )
    payload = [
        {
            "id": r[0],
            "event_type": r[1],
            "kid": r[2],
            "detail_json": r[3],
            "created_at": r[4],
        }
        for r in rows
    ]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def _pub_pem(kid: str) -> str:
    row = _db_rows("SELECT public_pem FROM signing_keys WHERE kid = ?", (kid,))
    assert len(row) == 1
    return str(row[0][0])


def _b64url_json(segment: str) -> dict:
    import base64

    pad = "=" * ((4 - len(segment) % 4) % 4)
    return json.loads(base64.urlsafe_b64decode(segment + pad))


def _verify_rs256(token: str, kid: str) -> bool:
    import base64

    parts = token.split(".")
    if len(parts) != 3 or not parts[2]:
        return False
    header = _b64url_json(parts[0])
    payload = _b64url_json(parts[1])
    if header.get("kid") != kid or header.get("alg") != "RS256":
        return False
    pad = "=" * ((4 - len(parts[2]) % 4) % 4)
    sig = base64.urlsafe_b64decode(parts[2] + pad)
    pub = serialization.load_pem_public_key(_pub_pem(kid).encode())
    data = (parts[0] + "." + parts[1]).encode()
    try:
        pub.verify(sig, data, padding.PKCS1v15(), hashes.SHA256())
    except Exception:
        return False
    now = int(time.time())
    return (
        payload.get("iss") == "vault-edge"
        and int(payload.get("nbf", 0)) <= now
        and int(payload.get("exp", 0)) >= now
    )


def _mint_rs256_token(kid: str, private_pem_path: pathlib.Path, subject: str = "operator") -> str:
    import base64

    rt = json.loads(RUNTIME.read_text(encoding="utf-8"))
    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT", "kid": kid}
    payload = {
        "iss": rt["issuer"],
        "sub": subject,
        "iat": now,
        "nbf": now,
        "exp": now + 3600,
    }

    def b64url(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    h = b64url(json.dumps(header, separators=(",", ":")).encode())
    p = b64url(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{h}.{p}".encode()
    key = serialization.load_pem_private_key(private_pem_path.read_bytes(), password=None)
    sig = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    return f"{h}.{p}.{b64url(sig)}"


def _echo_status(token: str) -> int:
    rt = json.loads(RUNTIME.read_text(encoding="utf-8"))
    req = urllib.request.Request(
        f"{rt['api_base']}/resource/echo",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


def _reset_pre_rotation_db() -> None:
    bootstrap = pathlib.Path("/app/data/bootstrap")
    priv = (bootstrap / "key-001.pem").read_text(encoding="utf-8")
    pub = (bootstrap / "key-001.pub.pem").read_text(encoding="utf-8")
    conn = sqlite3.connect(DB)
    try:
        conn.execute("DELETE FROM audit_log")
        conn.execute("DELETE FROM signing_keys")
        conn.execute(
            "INSERT INTO signing_keys (kid, public_pem, private_pem, status, created_at) "
            "VALUES (?, ?, ?, 'active', ?)",
            ("key-001", pub, priv, "1970-01-01T00:00:00+00:00"),
        )
        conn.commit()
    finally:
        conn.close()


def _login_token() -> str:
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


@pytest.fixture(autouse=True, scope="session")
def ensure_api_running():
    subprocess.run(
        ["bash", "/app/scripts/start-api.sh"],
        check=True,
        timeout=15,
    )


class TestMilestone3:
    def test_rotation_audit_required_fields(self):
        """Verify rotation audit required fields."""
        assert REQUIRED.issubset(_load_audit().keys())

    def test_rotation_success_flags(self):
        """Verify rotation success flags."""
        data = _load_audit()
        assert data["rotated"] is True
        assert data["verify_after_rotate"] is True
        assert data["pre_rotate_token_valid"] is True
        assert data["previous_private_cleared"] is True
        assert data["audit_sequence_ok"] is True
        assert data["pre_crypto_ok"] is True
        assert data["post_crypto_ok"] is True
        assert data["audit_rows"] >= 2
        assert data["signing_key_row_count"] == 2
        pre_token = _mint_rs256_token("key-001", BOOTSTRAP_KEY)
        assert _verify_rs256(pre_token, "key-001")
        pub = _pub_pem("key-001")
        assert pub and "BEGIN" in pub
        assert _echo_status(pre_token) == 200
        post_token = _login_token()
        assert _verify_rs256(post_token, data["active_kid"])

    def test_kid_transition_consistency(self):
        """Verify kid transition consistency."""
        data = _load_audit()
        assert data["previous_kid"] == "key-001"
        assert data["active_kid"] == "key-002"
        assert data["pre_rotate_kid"] == data["previous_kid"]
        assert data["post_rotate_kid"] == data["active_kid"]

    def test_signing_keys_status_invariants(self):
        """Verify signing keys status invariants."""
        data = _load_audit()
        active = _db_rows("SELECT kid FROM signing_keys WHERE status = 'active'")
        previous = _db_rows("SELECT kid FROM signing_keys WHERE status = 'previous'")
        assert len(active) == 1 and active[0][0] == data["active_kid"]
        assert len(previous) == 1 and previous[0][0] == data["previous_kid"]
        assert data["previous_row_count"] == 1

    def test_previous_private_cleared_in_db(self):
        """Verify previous private cleared in db."""
        data = _load_audit()
        row = _db_rows(
            "SELECT private_pem FROM signing_keys WHERE kid = ?",
            (data["previous_kid"],),
        )
        assert row[0][0] in (None, "")

    def test_active_retains_private_material(self):
        """Verify active retains private material."""
        data = _load_audit()
        row = _db_rows(
            "SELECT private_pem FROM signing_keys WHERE kid = ?",
            (data["active_kid"],),
        )
        assert row[0][0] and "BEGIN" in str(row[0][0])

    def test_jwks_lists_previous_and_active(self):
        """Verify jwks lists previous and active."""
        data = _load_audit()
        kids = data["jwks_kids"]
        assert kids == sorted(kids)
        assert set(kids) == {data["previous_kid"], data["active_kid"]}

    def test_live_jwks_endpoint_matches_database(self):
        """Verify live JWKS publication matches database after rotation."""
        data = _load_audit()
        rt = json.loads(RUNTIME.read_text(encoding="utf-8"))
        with urllib.request.urlopen(
            f"{rt['api_base']}/.well-known/jwks.json", timeout=5
        ) as resp:
            jwks = json.load(resp)
        live_kids = sorted(k["kid"] for k in jwks.get("keys", []) if "kid" in k)
        db_kids = sorted(
            r[0]
            for r in _db_rows(
                "SELECT kid FROM signing_keys WHERE status IN ('active','previous')"
            )
        )
        assert live_kids == db_kids
        assert set(live_kids) == {data["previous_kid"], data["active_kid"]}

    def test_audit_log_events_order_and_payloads(self):
        """Verify audit log events order and payloads."""
        data = _load_audit()
        rows = _db_rows(
            "SELECT event_type, kid, detail_json FROM audit_log ORDER BY id ASC"
        )
        types = [r[0] for r in rows]
        assert types.index("key_retired") < types.index("key_promoted")
        retired = json.loads(rows[types.index("key_retired")][2])
        promoted = json.loads(rows[types.index("key_promoted")][2])
        assert retired["successor"] == data["active_kid"]
        assert promoted["from"] == data["previous_kid"]

    def test_audit_chain_digest_matches_db(self):
        """Verify audit chain digest matches db."""
        data = _load_audit()
        assert data["audit_chain_digest"] == _audit_chain_digest()

    def test_post_login_token_verifies_with_active_key(self):
        """Verify post login token verifies with active key."""
        data = _load_audit()
        token = _login_token()
        assert _verify_rs256(token, data["active_kid"])

    def test_pre_rotate_kid_differs_from_post(self):
        """Verify pre rotate kid differs from post."""
        data = _load_audit()
        assert data["pre_rotate_kid"] != data["post_rotate_kid"]

    def test_no_extra_signing_key_rows(self):
        """Verify no extra signing key rows."""
        assert len(_db_rows("SELECT kid FROM signing_keys")) == 2

    def test_pre_rotate_token_grace_period(self):
        """Verify a key-001-signed bearer is accepted after rotation."""
        data = _load_audit()
        assert data["previous_kid"] == "key-001"
        pre_token = _mint_rs256_token("key-001", BOOTSTRAP_KEY)
        assert _verify_rs256(pre_token, data["previous_kid"])
        assert _echo_status(pre_token) == 200

    def test_z_guardctl_rotate_cli_succeeds(self):
        """Run guardctl rotate on a pre-rotation DB and verify it succeeds."""
        if AUDIT.exists():
            AUDIT.unlink()
        _reset_pre_rotation_db()
        subprocess.run(
            ["bash", "/app/scripts/start-api.sh"],
            check=True,
            timeout=15,
        )
        result = subprocess.run(
            ["/app/cli/guardctl", "rotate"],
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr.decode()
        assert AUDIT.exists()
        data = _load_audit()
        assert data["rotated"] is True
        assert data["active_kid"] == "key-002"
        assert data["previous_kid"] == "key-001"
