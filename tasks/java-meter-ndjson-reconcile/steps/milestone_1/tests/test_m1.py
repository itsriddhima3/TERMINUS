"""Milestone 1 — meter batch fetch (paginated stream + UTC timestamp checks)."""

import hashlib
import json
import subprocess
import time
import urllib.request
from pathlib import Path

READINGS = Path("/app/var/readings.json")
BATCH = "MTR-2024-Q1"
API = "http://127.0.0.1:8080"
READING_KEYS = {"device_id", "reading_at", "register_kwh", "interval_min"}

# Stream order across both paginated pages (page 0 then page 1).
EXPECTED_READINGS = [
    {
        "device_id": "DEV-A01",
        "reading_at": "2024-01-01T00:00:00Z",
        "register_kwh": 100.0,
        "interval_min": 15,
    },
    {
        "device_id": "DEV-A01",
        "reading_at": "2024-01-01T00:15:00Z",
        "register_kwh": 100.25,
        "interval_min": 15,
    },
    {
        "device_id": "DEV-A02",
        "reading_at": "2024-01-01T00:00:00Z",
        "register_kwh": 50.0,
        "interval_min": 15,
    },
    {
        "device_id": "DEV-A02",
        "reading_at": "2024-01-01T00:30:00Z",
        "register_kwh": 50.5,
        "interval_min": 15,
    },
    {
        "device_id": "DEV-B01",
        "reading_at": "2024-01-01T00:00:00Z",
        "register_kwh": 200.0,
        "interval_min": 15,
    },
    {
        "device_id": "DEV-B01",
        "reading_at": "2024-01-01T00:15:00Z",
        "register_kwh": 201.5,
        "interval_min": 15,
    },
    {
        "device_id": "DEV-A01",
        "reading_at": "2024-01-01T00:30:00Z",
        "register_kwh": 100.5,
        "interval_min": 15,
    },
    {
        "device_id": "DEV-A01",
        "reading_at": "2024-01-01T00:30:00Z",
        "register_kwh": 105.0,
        "interval_min": 15,
    },
]


def _ensure_api() -> None:
    try:
        urllib.request.urlopen(f"{API}/health", timeout=1).read()
        return
    except Exception:
        pass
    subprocess.run(["/app/scripts/start-api.sh"], check=False, capture_output=True)
    deadline = time.time() + 8.0
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{API}/health", timeout=1).read()
            return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError("meter api not reachable on port 8080")


def _run_fetch() -> subprocess.CompletedProcess:
    _ensure_api()
    return subprocess.run(
        ["/app/bin/meterctl", "fetch", BATCH],
        capture_output=True,
        timeout=30,
    )


def _load() -> dict:
    if not READINGS.is_file():
        result = _run_fetch()
        assert result.returncode == 0, result.stderr.decode()
    return json.loads(READINGS.read_text(encoding="utf-8"))


def _canonical_digest(doc: dict) -> str:
    payload = json.dumps(doc, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def _live_stream_readings() -> list[dict]:
    """Pull both paginated stream pages directly from the service."""
    readings: list[dict] = []
    cursor = ""
    while True:
        url = f"{API}/api/v1/readings/stream?meterId={BATCH}&cursor={cursor}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
            next_cursor = resp.headers.get("X-Next-Cursor") or ""
        for line in body.splitlines():
            trimmed = line.strip()
            if trimmed:
                readings.append(json.loads(trimmed))
        if not next_cursor:
            break
        cursor = next_cursor
    return readings


class TestMilestone1:
    def test_m1_meter_id_and_reading_count(self):
        """Fetch writes meter_id MTR-2024-Q1 with eight readings."""
        doc = _load()
        assert doc["meter_id"] == BATCH
        assert len(doc["readings"]) == 8

    def test_m1_readings_match_stream_contract(self):
        """Every persisted row matches the bench stream table."""
        doc = _load()
        assert doc["meter_id"] == BATCH
        assert len(doc["readings"]) == len(EXPECTED_READINGS)
        for got, exp in zip(doc["readings"], EXPECTED_READINGS, strict=True):
            assert got == exp

    def test_m1_reading_order_stable(self):
        """Rows follow API stream order (page zero then page one)."""
        doc = _load()
        assert [r["device_id"] for r in doc["readings"]] == [
            r["device_id"] for r in EXPECTED_READINGS
        ]
        assert doc["readings"][0]["device_id"] == "DEV-A01"
        assert doc["readings"][-1]["register_kwh"] == 105.0

    def test_m1_reading_schema_strict(self):
        """Rows expose only the four contract fields with JSON-safe types."""
        doc = _load()
        for row in doc["readings"]:
            assert set(row.keys()) == READING_KEYS
            assert isinstance(row["device_id"], str)
            assert isinstance(row["reading_at"], str)
            assert isinstance(row["register_kwh"], (int, float))
            assert isinstance(row["interval_min"], int)

    def test_m1_utc_z_suffix_all_rows(self):
        """reading_at values keep the trailing Z UTC suffix."""
        doc = _load()
        for row in doc["readings"]:
            assert row["reading_at"].endswith("Z"), row["reading_at"]

    def test_m1_dev_a01_first_register(self):
        """First row is DEV-A01 at midnight with register 100.0."""
        doc = _load()
        first = doc["readings"][0]
        assert first["device_id"] == "DEV-A01"
        assert first["reading_at"] == "2024-01-01T00:00:00Z"
        assert first["register_kwh"] == 100.0
        assert first["interval_min"] == 15

    def test_m1_page_two_rows_present(self):
        """Second page rows (DEV-B01 00:15 onward) are present."""
        doc = _load()
        ids = [r["device_id"] for r in doc["readings"]]
        assert ids.count("DEV-B01") == 2
        assert doc["readings"][5]["device_id"] == "DEV-B01"
        assert doc["readings"][5]["reading_at"] == "2024-01-01T00:15:00Z"

    def test_m1_not_reversed_wire_order(self):
        """Ingest cannot satisfy stream order when rows are reversed."""
        doc = _load()
        assert doc["readings"][0]["reading_at"] == "2024-01-01T00:00:00Z"
        assert doc["readings"][-1]["reading_at"] == "2024-01-01T00:30:00Z"
        assert doc["readings"][-1]["register_kwh"] == 105.0

    def test_m1_duplicate_timestamp_row_kept(self):
        """Both DEV-A01 rows at 00:30 survive with distinct registers."""
        doc = _load()
        half_hour = [
            r for r in doc["readings"] if r["device_id"] == "DEV-A01" and "00:30:00" in r["reading_at"]
        ]
        assert len(half_hour) == 2
        assert {r["register_kwh"] for r in half_hour} == {100.5, 105.0}

    def test_m1_interval_min_fifteen(self):
        """Every row records a fifteen-minute interval."""
        doc = _load()
        assert all(r["interval_min"] == 15 for r in doc["readings"])

    def test_m1_readings_checksum_stable(self):
        """Canonical readings digest is stable across reruns."""
        _run_fetch()
        first = _canonical_digest(_load())
        _run_fetch()
        second = _canonical_digest(_load())
        assert first == second
        assert len(first) == 64

    def test_m1_fetch_cli_exit_zero(self):
        """fetch succeeds from a clean slate and writes readings.json."""
        if READINGS.exists():
            READINGS.unlink()
        result = _run_fetch()
        assert result.returncode == 0, result.stderr.decode()
        assert READINGS.is_file()

    def test_m1_dev_a02_gap_row_register(self):
        """DEV-A02 00:30 register is 50.5 after the missing quarter-hour slot."""
        doc = _load()
        row = next(
            r for r in doc["readings"] if r["device_id"] == "DEV-A02" and "00:30:00" in r["reading_at"]
        )
        assert row["register_kwh"] == 50.5

    def test_m1_dev_b01_impossible_delta_raw(self):
        """DEV-B01 00:15 register is 201.5 in the persisted stream."""
        doc = _load()
        row = next(
            r for r in doc["readings"] if r["device_id"] == "DEV-B01" and "00:15:00" in r["reading_at"]
        )
        assert row["register_kwh"] == 201.5

    def test_m1_device_ids_complete_set(self):
        """All three bench devices appear in the captured batch."""
        doc = _load()
        assert {r["device_id"] for r in doc["readings"]} == {"DEV-A01", "DEV-A02", "DEV-B01"}

    def test_m1_live_api_pages_match_file(self):
        """Persisted rows match a manual two-page pull from the stream endpoint."""
        doc = _load()
        live = _live_stream_readings()
        assert len(live) == len(EXPECTED_READINGS) == 8
        for got, wire in zip(doc["readings"], live, strict=True):
            assert got["device_id"] == wire["device_id"]
            assert got["reading_at"] == wire["reading_at"]
            assert got["register_kwh"] == wire["register_kwh"]
            assert got["interval_min"] == wire["interval_min"]
