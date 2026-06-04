"""Milestone 1 — service map contract (strict cross-checks)."""

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

MAP = pathlib.Path("/app/output/service_map.json")
DB = "/app/var/vault.db"
RUNTIME = pathlib.Path("/app/platform/runtime.json")

EXPECTED_ENDPOINTS = [
    ("GET", "/health", False),
    ("POST", "/auth/login", False),
    ("GET", "/resource/echo", True),
    ("GET", "/.well-known/jwks.json", False),
]

TABLE_COLUMNS = {
    "audit_log": ["created_at", "detail_json", "event_type", "id", "kid"],
    "signing_keys": ["created_at", "kid", "private_pem", "public_pem", "status"],
    "users": ["id", "pass_hash", "username"],
}

ALLOWED_TOP = {
    "base_url",
    "health_ok",
    "endpoints",
    "tables",
    "active_kid",
    "jwks_kids",
    "login_probe_ok",
    "schema_fingerprint",
    "status_histogram",
    "active_pubkey_digest",
    "jwks_bundle_digest",
    "login_issuer",
    "login_crypto_ok",
}


def _load_map() -> dict:
    assert MAP.exists(), f"missing {MAP}"
    with MAP.open(encoding="utf-8") as fh:
        data = json.load(fh)
    assert isinstance(data, dict)
    return data


def _live_schema() -> dict[str, list[str]]:
    conn = sqlite3.connect(DB)
    try:
        out: dict[str, list[str]] = {}
        for table in TABLE_COLUMNS:
            cols = sorted(r[1] for r in conn.execute(f"PRAGMA table_info({table})"))
            out[table] = cols
        return out
    finally:
        conn.close()


def _schema_fingerprint(tables: dict[str, list[str]]) -> str:
    parts = [f"{name}:{','.join(cols)}" for name, cols in sorted(tables.items())]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def _fetch_jwks(base_url: str) -> dict:
    with urllib.request.urlopen(f"{base_url}/.well-known/jwks.json", timeout=5) as resp:
        return json.load(resp)


def _active_row() -> tuple[str, str]:
    conn = sqlite3.connect(DB)
    try:
        row = conn.execute(
            "SELECT kid, public_pem FROM signing_keys WHERE status = 'active' LIMIT 1"
        ).fetchone()
        assert row is not None
        return str(row[0]), str(row[1])
    finally:
        conn.close()


@pytest.fixture(autouse=True, scope="session")
def ensure_api_running():
    subprocess.run(
        ["bash", "/app/scripts/start-api.sh"],
        check=True,
        timeout=15,
    )


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
    conn = sqlite3.connect(DB)
    try:
        row = conn.execute(
            "SELECT public_pem FROM signing_keys WHERE kid = ?", (kid,)
        ).fetchone()
        assert row is not None
        pub_pem = str(row[0])
    finally:
        conn.close()
    pub = serialization.load_pem_public_key(pub_pem.encode())
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


def _assert_login_crypto_independent(base_url: str) -> None:
    kid, _ = _active_row()
    token = _login_token(base_url)
    assert _verify_rs256(token, kid), "login token must verify with active RSA public key"


def _login_token(base_url: str) -> str:
    rt = json.loads(RUNTIME.read_text(encoding="utf-8"))
    payload = json.dumps(
        {"username": rt["login_user"], "password": rt["login_password"]}
    ).encode()
    req = urllib.request.Request(
        f"{base_url}/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        body = json.load(resp)
    return str(body["access_token"])


class TestMilestone1:
    def test_guardctl_map_produces_valid_output(self):
        """Verify guardctl map generates a correct service map artifact."""
        if MAP.exists():
            MAP.unlink()
        result = subprocess.run(
            ["/app/cli/guardctl", "map"],
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr.decode()
        assert MAP.exists(), "guardctl map did not produce output"
        data = _load_map()
        assert data["health_ok"] is True
        assert data["login_probe_ok"] is True
        assert data["login_crypto_ok"] is True
        _assert_login_crypto_independent(data["base_url"])

    def test_map_required_top_level_fields(self):
        """Verify map required top level fields."""
        data = _load_map()
        assert ALLOWED_TOP.issubset(data.keys())

    def test_no_extra_top_level_keys(self):
        """Verify no extra top level keys."""
        assert set(_load_map().keys()) == ALLOWED_TOP

    def test_health_login_and_crypto_flags(self):
        """Verify health login and crypto flags."""
        data = _load_map()
        assert data["health_ok"] is True
        assert data["login_probe_ok"] is True
        assert data["login_crypto_ok"] is True
        assert data["login_issuer"] == "vault-edge"
        _assert_login_crypto_independent(data["base_url"])

    def test_base_url_matches_runtime(self):
        """Verify base url matches runtime."""
        data = _load_map()
        rt = json.loads(RUNTIME.read_text(encoding="utf-8"))
        assert data["base_url"] == rt["api_base"]

    def test_endpoints_exact_catalog_sorted(self):
        """Verify endpoints exact catalog sorted."""
        data = _load_map()
        seen = {(e["method"], e["path"], e["auth"]) for e in data["endpoints"]}
        assert seen == set(EXPECTED_ENDPOINTS)
        paths = [e["path"] for e in data["endpoints"]]
        assert paths == sorted(paths)
        for entry in data["endpoints"]:
            assert set(entry.keys()) == {"method", "path", "auth"}

    def test_tables_sorted_and_match_live_schema(self):
        """Verify tables sorted and match live schema."""
        data = _load_map()
        live = _live_schema()
        assert list(data["tables"].keys()) == sorted(data["tables"].keys())
        assert data["tables"] == live
        for table, cols in TABLE_COLUMNS.items():
            assert data["tables"][table] == cols

    def test_schema_fingerprint_matches_live_digest(self):
        """Verify schema fingerprint matches live digest."""
        data = _load_map()
        live = _live_schema()
        assert data["schema_fingerprint"] == _schema_fingerprint(live)
        assert len(data["schema_fingerprint"]) == 64

    def test_status_histogram_pre_rotation(self):
        """Verify status histogram pre rotation."""
        data = _load_map()
        hist = data["status_histogram"]
        assert hist.get("active", 0) == 1
        assert hist.get("previous", 0) == 0
        assert sum(hist.values()) == 1

    def test_active_kid_and_jwks_alignment(self):
        """Verify active kid and jwks alignment."""
        data = _load_map()
        kid, _ = _active_row()
        assert data["active_kid"] == kid
        jwks = _fetch_jwks(data["base_url"])
        kids = sorted(k["kid"] for k in jwks.get("keys", []) if "kid" in k)
        assert data["jwks_kids"] == kids == [kid]
        for entry in jwks["keys"]:
            assert entry["kty"] == "RSA"
            assert entry["alg"] == "RS256"
            assert entry["use"] == "sig"

    def test_pubkey_and_jwks_digests(self):
        """Verify pubkey and jwks digests."""
        data = _load_map()
        kid, pem = _active_row()
        assert data["active_pubkey_digest"] == hashlib.sha256(pem.encode()).hexdigest()
        jwks = _fetch_jwks(data["base_url"])
        assert data["jwks_bundle_digest"] == hashlib.sha256(
            json.dumps(jwks["keys"], separators=(",", ":")).encode()
        ).hexdigest()

    def test_login_token_issuer_claim(self):
        """Verify login token issuer claim."""
        import base64

        data = _load_map()
        now = int(time.time())
        token = _login_token(data["base_url"])
        seg = token.split(".")[1]
        pad = "=" * ((4 - len(seg) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(seg + pad))
        assert payload["iss"] == data["login_issuer"] == "vault-edge"
        assert payload["exp"] > now

    def test_service_map_file_is_valid_json_line(self):
        """Verify service map file is valid json line."""
        raw = MAP.read_text(encoding="utf-8")
        assert raw.endswith("\n")
        assert json.loads(raw.strip()) == _load_map()
