"""Milestone 2 — device/tariff enrichment and correction application."""

import csv
import json
import subprocess
import time
import urllib.request
from pathlib import Path

NORMALIZED = Path("/app/var/normalized.json")
READINGS = Path("/app/var/readings.json")
DEVICES_CSV = Path("/app/data/devices.csv")
TARIFFS_CSV = Path("/app/data/tariffs.csv")
BATCH = "MTR-2024-Q1"
API = "http://127.0.0.1:8080"

FETCH_KEYS = {"device_id", "reading_at", "register_kwh", "interval_min"}
ENRICH_KEYS = FETCH_KEYS | {
    "site_id",
    "rate_cents",
    "max_delta_kwh_per_interval",
    "corrected_register_kwh",
}

DEVICES = {
    "DEV-A01": {"site_id": "SITE-NORTH", "max_delta_kwh_per_interval": 0.5},
    "DEV-A02": {"site_id": "SITE-NORTH", "max_delta_kwh_per_interval": 0.5},
    "DEV-B01": {"site_id": "SITE-SOUTH", "max_delta_kwh_per_interval": 1.0},
}

TARIFFS = [
    ("SITE-NORTH", "00:00", "06:00", 8.5),
    ("SITE-NORTH", "06:00", "22:00", 12.0),
    ("SITE-NORTH", "22:00", "24:00", 8.5),
    ("SITE-SOUTH", "00:00", "24:00", 10.0),
]

RAW_READINGS = [
    ("DEV-A01", "2024-01-01T00:00:00Z", 100.0),
    ("DEV-A01", "2024-01-01T00:15:00Z", 100.25),
    ("DEV-A02", "2024-01-01T00:00:00Z", 50.0),
    ("DEV-A02", "2024-01-01T00:30:00Z", 50.5),
    ("DEV-B01", "2024-01-01T00:00:00Z", 200.0),
    ("DEV-B01", "2024-01-01T00:15:00Z", 201.5),
    ("DEV-A01", "2024-01-01T00:30:00Z", 100.5),
    ("DEV-A01", "2024-01-01T00:30:00Z", 105.0),
]

CORRECTIONS = {
    ("DEV-A01", "2024-01-01T00:30:00Z"): -4.5,
}


def _clock_hhmm(reading_at: str) -> str:
    tail = reading_at.split("T", 1)[1]
    return tail[:5]


def _rate_for_site(site_id: str, reading_at: str) -> float:
    clock = _clock_hhmm(reading_at)
    for site, start, end, rate in TARIFFS:
        if site != site_id:
            continue
        if start <= clock < end:
            return rate
    return 0.0


def _expected_row(device_id: str, reading_at: str, register_kwh: float) -> dict:
    dev = DEVICES[device_id]
    site_id = dev["site_id"]
    corrected = register_kwh + CORRECTIONS.get((device_id, reading_at), 0.0)
    return {
        "device_id": device_id,
        "reading_at": reading_at,
        "register_kwh": register_kwh,
        "interval_min": 15,
        "site_id": site_id,
        "rate_cents": _rate_for_site(site_id, reading_at),
        "max_delta_kwh_per_interval": dev["max_delta_kwh_per_interval"],
        "corrected_register_kwh": corrected,
    }


def _expected_normalized() -> dict:
    readings = [
        _expected_row(device_id, reading_at, register_kwh)
        for device_id, reading_at, register_kwh in RAW_READINGS
    ]
    return {"meter_id": BATCH, "readings": readings}


def _api_json(path: str) -> object:
    raw = urllib.request.urlopen(f"{API}{path}", timeout=5).read()
    return json.loads(raw)


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


def _run_fetch_enrich() -> None:
    _ensure_api()
    subprocess.run(
        ["/app/bin/meterctl", "fetch", BATCH],
        check=True,
        capture_output=True,
        timeout=30,
    )
    subprocess.run(
        ["/app/bin/meterctl", "normalize", BATCH],
        check=True,
        capture_output=True,
        timeout=30,
    )


def _load() -> dict:
    if not NORMALIZED.is_file():
        _run_fetch_enrich()
    return json.loads(NORMALIZED.read_text(encoding="utf-8"))


def _row(doc: dict, device_id: str, reading_at: str) -> dict:
    matches = [
        r
        for r in doc["readings"]
        if r["device_id"] == device_id and r["reading_at"] == reading_at
    ]
    assert len(matches) == 1, f"expected one row for {device_id} {reading_at}"
    return matches[0]


def _rows(doc: dict, device_id: str, reading_at: str) -> list[dict]:
    return [
        r
        for r in doc["readings"]
        if r["device_id"] == device_id and r["reading_at"] == reading_at
    ]


def _live_corrections() -> dict[tuple[str, str], float]:
    payload = _api_json(f"/api/v1/corrections?meterId={BATCH}")
    out: dict[tuple[str, str], float] = {}
    for item in payload:
        key = (item["device_id"], item["reading_at"])
        out[key] = float(item["delta_kwh"])
    return out


class TestMilestone2:
    def test_m2_meter_id_and_row_count(self):
        """Normalization retains meter_id MTR-2024-Q1 with eight rows."""
        doc = _load()
        assert doc["meter_id"] == BATCH
        assert len(doc["readings"]) == 8

    def test_m2_rows_match_enrichment_contract(self):
        """Every row matches device join, tariff window, and correction math."""
        doc = _load()
        expected = _expected_normalized()
        assert doc["meter_id"] == expected["meter_id"]
        assert len(doc["readings"]) == len(expected["readings"])
        for got, exp in zip(doc["readings"], expected["readings"], strict=True):
            assert got == exp

    def test_m2_site_north_dev_a01(self):
        """DEV-A01 rows carry SITE-NORTH from the device catalog."""
        doc = _load()
        for row in doc["readings"]:
            if row["device_id"] == "DEV-A01":
                assert row["site_id"] == "SITE-NORTH"

    def test_m2_site_south_dev_b01(self):
        """DEV-B01 rows carry SITE-SOUTH from the device catalog."""
        doc = _load()
        for row in doc["readings"]:
            if row["device_id"] == "DEV-B01":
                assert row["site_id"] == "SITE-SOUTH"

    def test_m2_rate_off_peak_north(self):
        """Midnight SITE-NORTH readings use the 8.5 off-peak band."""
        doc = _load()
        row = _row(doc, "DEV-A01", "2024-01-01T00:00:00Z")
        assert row["rate_cents"] == 8.5

    def test_m2_rate_south_all_day(self):
        """SITE-SOUTH readings use the flat 10.0 rate."""
        doc = _load()
        row = _row(doc, "DEV-B01", "2024-01-01T00:15:00Z")
        assert row["rate_cents"] == 10.0

    def test_m2_exclusive_window_not_midday_rate(self):
        """00:30 SITE-NORTH must not pick the 12.0 daytime band."""
        doc = _load()
        row = _row(doc, "DEV-A02", "2024-01-01T00:30:00Z")
        assert row["rate_cents"] == 8.5
        assert row["rate_cents"] != 12.0

    def test_m2_correction_dev_a01_half_hour(self):
        """Ledger delta -4.5 adjusts both DEV-A01 rows at 00:30 independently."""
        doc = _load()
        rows = _rows(doc, "DEV-A01", "2024-01-01T00:30:00Z")
        assert len(rows) == 2
        by_register = {r["register_kwh"]: r["corrected_register_kwh"] for r in rows}
        assert by_register[100.5] == 96.0
        assert by_register[105.0] == 100.5

    def test_m2_max_delta_limits_from_catalog(self):
        """max_delta_kwh_per_interval matches devices.csv per device."""
        doc = _load()
        for row in doc["readings"]:
            assert row["max_delta_kwh_per_interval"] == DEVICES[row["device_id"]][
                "max_delta_kwh_per_interval"
            ]

    def test_m2_live_corrections_api(self):
        """corrected_register_kwh reflects live ledger deltas on every row at a stamp."""
        doc = _load()
        live = _live_corrections()
        assert live[("DEV-A01", "2024-01-01T00:30:00Z")] == -4.5
        for row in doc["readings"]:
            key = (row["device_id"], row["reading_at"])
            delta = live.get(key, 0.0)
            assert row["corrected_register_kwh"] == row["register_kwh"] + delta

    def test_m2_ledger_not_single_apply_on_duplicate_stamp(self):
        """Second DEV-A01 00:30 row must not remain at raw 105.0 after ledger pass."""
        doc = _load()
        rows = _rows(doc, "DEV-A01", "2024-01-01T00:30:00Z")
        high_row = next(r for r in rows if r["register_kwh"] == 105.0)
        assert high_row["corrected_register_kwh"] == 100.5
        assert high_row["corrected_register_kwh"] != high_row["register_kwh"]

    def test_m2_preserves_fetch_columns(self):
        """Enrichment must not mutate fetch columns."""
        _ensure_api()
        fetch_doc = json.loads(Path("/app/var/readings.json").read_text(encoding="utf-8"))
        if not fetch_doc.get("readings"):
            _run_fetch_enrich()
            fetch_doc = json.loads(Path("/app/var/readings.json").read_text(encoding="utf-8"))
        _run_fetch_enrich()
        doc = _load()
        for fetch_row, norm_row in zip(fetch_doc["readings"], doc["readings"], strict=True):
            for key in FETCH_KEYS:
                assert norm_row[key] == fetch_row[key]

    def test_m2_enriched_row_schema(self):
        """Rows include enrichment keys with consistent typing."""
        doc = _load()
        for row in doc["readings"]:
            assert set(row.keys()) == ENRICH_KEYS
            assert isinstance(row["site_id"], str) and row["site_id"]
            assert isinstance(row["rate_cents"], (int, float))
            assert isinstance(row["max_delta_kwh_per_interval"], (int, float))
            assert isinstance(row["corrected_register_kwh"], (int, float))

    def test_m2_enrich_idempotent(self):
        """Two normalize runs produce identical JSON bytes."""
        _run_fetch_enrich()
        first = NORMALIZED.read_bytes()
        subprocess.run(
            ["/app/bin/meterctl", "normalize", BATCH],
            check=True,
            capture_output=True,
            timeout=30,
        )
        assert NORMALIZED.read_bytes() == first

    def test_m2_uncorrected_rows_passthrough(self):
        """Rows without correction events keep corrected_register_kwh equal to register_kwh."""
        doc = _load()
        row = _row(doc, "DEV-B01", "2024-01-01T00:00:00Z")
        assert row["register_kwh"] == 200.0
        assert row["corrected_register_kwh"] == 200.0

    def test_m2_device_csv_join_keys(self):
        """Device catalog join keys on device_id, not site_id."""
        with DEVICES_CSV.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        assert {r["device_id"] for r in rows} == set(DEVICES)

    def test_m2_tariff_csv_windows_loaded(self):
        """Tariff helper sees four windows including SITE-SOUTH all-day."""
        with TARIFFS_CSV.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 4
        south = next(r for r in rows if r["site_id"] == "SITE-SOUTH")
        assert float(south["rate_cents"]) == 10.0

    def test_m2_no_correction_on_dev_a02(self):
        """DEV-A02 registers remain uncorrected."""
        doc = _load()
        row = _row(doc, "DEV-A02", "2024-01-01T00:30:00Z")
        assert row["corrected_register_kwh"] == row["register_kwh"] == 50.5

    def test_m2_register_mutation_recomputes_correction(self):
        """Raising a raw register re-applies the live -4.5 correction delta at 00:30."""
        _run_fetch_enrich()
        snapshot = READINGS.read_text(encoding="utf-8")
        try:
            readings_doc = json.loads(snapshot)
            target = next(
                r
                for r in readings_doc["readings"]
                if r["device_id"] == "DEV-A01"
                and r["reading_at"] == "2024-01-01T00:30:00Z"
                and r["register_kwh"] == 100.5
            )
            target["register_kwh"] = 110.0
            READINGS.write_text(json.dumps(readings_doc, separators=(",", ":")), encoding="utf-8")
            subprocess.run(
                ["/app/bin/meterctl", "normalize", BATCH],
                check=True,
                capture_output=True,
                timeout=30,
            )
            doc = json.loads(NORMALIZED.read_text(encoding="utf-8"))
            row = next(
                r
                for r in doc["readings"]
                if r["device_id"] == "DEV-A01"
                and r["reading_at"] == "2024-01-01T00:30:00Z"
                and r["register_kwh"] == 110.0
            )
            assert row["corrected_register_kwh"] == 105.5
            other = next(
                r
                for r in doc["readings"]
                if r["device_id"] == "DEV-A01"
                and r["reading_at"] == "2024-01-01T00:30:00Z"
                and r["register_kwh"] == 105.0
            )
            assert other["corrected_register_kwh"] == 100.5
        finally:
            READINGS.write_text(snapshot, encoding="utf-8")
            subprocess.run(
                ["/app/bin/meterctl", "normalize", BATCH],
                check=True,
                capture_output=True,
                timeout=30,
            )

    def test_m2_north_rows_never_use_south_flat_rate(self):
        """SITE-NORTH rows must not inherit the SITE-SOUTH 10.0 fallback band."""
        doc = _load()
        for row in doc["readings"]:
            if row["site_id"] != "SITE-NORTH":
                continue
            assert row["rate_cents"] != 10.0
            assert row["rate_cents"] == _rate_for_site("SITE-NORTH", row["reading_at"])
