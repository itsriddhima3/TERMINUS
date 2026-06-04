"""Milestone 3 — interval anomaly reports and site cost roll-ups."""

import csv
import json
import subprocess
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

REPORT_JSON = Path("/app/output/reconcile.json")
NORMALIZED_CSV = Path("/app/output/normalized.csv")
NORMALIZED = Path("/app/var/normalized.json")
BATCH = "MTR-2024-Q1"
API = "http://127.0.0.1:8080"
TOL = 1e-6

# Expected cost roll-ups when corrections apply to every row at 00:30 (see delta_rules.md).
EXPECTED_COST = {
    "SITE-NORTH": 0.44625,
    "SITE-SOUTH": 0.15,
}


def _clock_minutes(ts: str) -> int:
    tail = ts.split("T", 1)[1]
    parts = tail.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def _minutes_between(a: str, b: str) -> int:
    return abs(_clock_minutes(b) - _clock_minutes(a))


def _missing_slot(ts: str, interval_min: int) -> str:
    date = ts.split("T", 1)[0]
    total = _clock_minutes(ts) + interval_min
    hour, minute = divmod(total, 60)
    return f"{date}T{hour:02d}:{minute:02d}:00Z"


def _compute_gap_events(readings: list[dict]) -> list[dict]:
    events: list[dict] = []
    by_device: dict[str, list[dict]] = defaultdict(list)
    for row in readings:
        by_device[row["device_id"]].append(row)
    for device_id, rows in by_device.items():
        rows.sort(key=lambda r: r["reading_at"])
        for idx in range(1, len(rows)):
            prev = rows[idx - 1]
            cur = rows[idx]
            prev_min = int(prev.get("interval_min", 15))
            gap_min = _minutes_between(prev["reading_at"], cur["reading_at"])
            if gap_min > prev_min:
                events.append(
                    {
                        "device_id": device_id,
                        "expected_at": _missing_slot(prev["reading_at"], prev_min),
                        "reading_at": cur["reading_at"],
                        "gap_minutes": gap_min - prev_min,
                    }
                )
    return events


def _compute_duplicate_events(readings: list[dict]) -> list[dict]:
    events: list[dict] = []
    seen: dict[str, int] = {}
    for row in readings:
        key = f"{row['device_id']}|{row['reading_at']}"
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > 1:
            events.append(
                {
                    "device_id": row["device_id"],
                    "reading_at": row["reading_at"],
                    "register_kwh": row["corrected_register_kwh"],
                }
            )
    return events


def _compute_delta_events(readings: list[dict]) -> list[dict]:
    events: list[dict] = []
    by_device: dict[str, list[dict]] = defaultdict(list)
    for row in readings:
        by_device[row["device_id"]].append(row)
    for device_id, rows in by_device.items():
        rows.sort(key=lambda r: r["reading_at"])
        for idx in range(1, len(rows)):
            prev = float(rows[idx - 1]["corrected_register_kwh"])
            cur = float(rows[idx]["corrected_register_kwh"])
            delta = cur - prev
            limit = float(rows[idx]["max_delta_kwh_per_interval"])
            if limit > 0 and delta > limit + 0.001:
                events.append(
                    {
                        "device_id": device_id,
                        "reading_at": rows[idx]["reading_at"],
                        "delta_kwh": delta,
                        "max_delta_kwh_per_interval": limit,
                    }
                )
    return events


def _compute_cost_by_site(readings: list[dict]) -> dict[str, float]:
    totals: dict[str, float] = {}
    by_device: dict[str, list[dict]] = defaultdict(list)
    for row in readings:
        by_device[row["device_id"]].append(row)
    for rows in by_device.values():
        rows.sort(key=lambda r: r["reading_at"])
        for idx in range(1, len(rows)):
            site = rows[idx]["site_id"]
            if not site:
                continue
            prev = float(rows[idx - 1]["corrected_register_kwh"])
            cur = float(rows[idx]["corrected_register_kwh"])
            kwh = max(0.0, cur - prev)
            rate = float(rows[idx]["rate_cents"])
            totals[site] = totals.get(site, 0.0) + kwh * rate / 100.0
    return totals


def _duplicate_timestamp_keys(dup_events: list[dict]) -> set[tuple[str, str]]:
    return {(ev["device_id"], ev["reading_at"]) for ev in dup_events}


def _expected_csv_issue(
    row: dict,
    gap_events: list[dict],
    dup_events: list[dict],
    delta_events: list[dict],
) -> str:
    device_id = row["device_id"]
    reading_at = row["reading_at"]
    for ev in gap_events:
        if ev["device_id"] == device_id and ev.get("reading_at") == reading_at:
            return "gap"
    if (device_id, reading_at) in _duplicate_timestamp_keys(dup_events):
        return "duplicate"
    for ev in delta_events:
        if ev["device_id"] == device_id and ev["reading_at"] == reading_at:
            return "impossible_delta"
    return ""


def _compute_expectations(normalized: dict) -> dict:
    readings = normalized["readings"]
    gaps = _compute_gap_events(readings)
    dups = _compute_duplicate_events(readings)
    deltas = _compute_delta_events(readings)
    costs = _compute_cost_by_site(readings)
    return {
        "meter_id": BATCH,
        "gap_events": gaps,
        "duplicate_events": dups,
        "impossible_delta_events": deltas,
        "cost_by_site": costs,
    }


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


def _run_pipeline() -> None:
    _ensure_api()
    for verb in ("fetch", "normalize", "reconcile"):
        subprocess.run(
            ["/app/bin/meterctl", verb, BATCH],
            check=True,
            capture_output=True,
            timeout=30,
        )


def _run_report_only() -> None:
    _ensure_api()
    subprocess.run(
        ["/app/bin/meterctl", "reconcile", BATCH],
        check=True,
        capture_output=True,
        timeout=30,
    )


def _load_normalized() -> dict:
    if not NORMALIZED.is_file():
        _run_pipeline()
    return json.loads(NORMALIZED.read_text(encoding="utf-8"))


def _load_json() -> dict:
    if not REPORT_JSON.is_file() or not NORMALIZED.is_file():
        _run_pipeline()
    return json.loads(REPORT_JSON.read_text(encoding="utf-8"))


def _load_csv_rows() -> list[dict]:
    if not NORMALIZED_CSV.is_file():
        _run_pipeline()
    return list(csv.DictReader(NORMALIZED_CSV.read_text(encoding="utf-8").splitlines()))


class TestMilestone3:
    def test_m3_gap_dev_a02(self):
        """gap_events lists DEV-A02 with expected_at 2024-01-01T00:15:00Z."""
        doc = _load_json()
        exp = _compute_expectations(_load_normalized())
        assert len(doc["gap_events"]) == len(exp["gap_events"]) == 1
        gap = doc["gap_events"][0]
        assert gap["device_id"] == "DEV-A02"
        assert gap["expected_at"] == "2024-01-01T00:15:00Z"

    def test_m3_duplicate_dev_a01(self):
        """duplicate_events flags DEV-A01 at 2024-01-01T00:30:00Z."""
        doc = _load_json()
        exp = _compute_expectations(_load_normalized())
        assert len(doc["duplicate_events"]) == len(exp["duplicate_events"]) == 1
        dup = doc["duplicate_events"][0]
        assert dup["device_id"] == "DEV-A01"
        assert dup["reading_at"] == "2024-01-01T00:30:00Z"

    def test_m3_impossible_delta_dev_b01(self):
        """impossible_delta_events includes DEV-B01 at 00:15 (+1.5 vs max 1.0)."""
        doc = _load_json()
        exp = _compute_expectations(_load_normalized())
        assert len(exp["impossible_delta_events"]) >= 1
        hit = next(
            ev
            for ev in doc["impossible_delta_events"]
            if ev["device_id"] == "DEV-B01" and ev["reading_at"] == "2024-01-01T00:15:00Z"
        )
        assert abs(hit["delta_kwh"] - 1.5) < TOL
        assert hit["max_delta_kwh_per_interval"] == 1.0

    def test_m3_impossible_delta_dev_a01_second_stamp(self):
        """Ledger-adjusted chain flags DEV-A01 second 00:30 row (+4.5 vs max 0.5)."""
        doc = _load_json()
        exp = _compute_expectations(_load_normalized())
        hit = next(
            ev
            for ev in doc["impossible_delta_events"]
            if ev["device_id"] == "DEV-A01"
            and ev["reading_at"] == "2024-01-01T00:30:00Z"
            and abs(ev["delta_kwh"] - 4.5) < TOL
        )
        assert hit["max_delta_kwh_per_interval"] == 0.5
        assert any(
            ev["device_id"] == "DEV-A01" and abs(ev["delta_kwh"] - 4.5) < TOL
            for ev in exp["impossible_delta_events"]
        )

    def test_m3_cost_site_north(self):
        """SITE-NORTH cost roll-up matches helper-derived interval energy totals."""
        doc = _load_json()
        exp = _compute_expectations(_load_normalized())
        assert abs(doc["cost_by_site"]["SITE-NORTH"] - exp["cost_by_site"]["SITE-NORTH"]) < TOL

    def test_m3_cost_site_south(self):
        """SITE-SOUTH cost roll-up matches helper-derived interval energy totals."""
        doc = _load_json()
        exp = _compute_expectations(_load_normalized())
        assert abs(doc["cost_by_site"]["SITE-SOUTH"] - exp["cost_by_site"]["SITE-SOUTH"]) < TOL

    def test_m3_cost_by_site_exact(self):
        """cost_by_site matches helper-derived totals for both sites."""
        doc = _load_json()
        exp = _compute_expectations(_load_normalized())
        for site, total in exp["cost_by_site"].items():
            assert abs(doc["cost_by_site"][site] - total) < TOL

    def test_m3_cost_includes_duplicate_stamp_interval(self):
        """SITE-NORTH roll-up bills the 4.5 kWh step between duplicate 00:30 stamps."""
        doc = _load_json()
        exp = _compute_expectations(_load_normalized())
        without_dup_step = exp["cost_by_site"]["SITE-NORTH"] - (4.5 * 8.5 / 100.0)
        assert doc["cost_by_site"]["SITE-NORTH"] > without_dup_step + TOL
        assert abs(doc["cost_by_site"]["SITE-NORTH"] - exp["cost_by_site"]["SITE-NORTH"]) < TOL

    def test_m3_csv_gap_issue_a02(self):
        """CSV issue column marks gap on DEV-A02 00:30 row."""
        exp = _compute_expectations(_load_normalized())
        rows = _load_csv_rows()
        target = next(
            r for r in rows if r["device_id"] == "DEV-A02" and r["reading_at"] == "2024-01-01T00:30:00Z"
        )
        assert target["issue"] == "gap"
        assert _expected_csv_issue(target, exp["gap_events"], exp["duplicate_events"], exp["impossible_delta_events"]) == "gap"

    def test_m3_csv_duplicate_both_a01(self):
        """CSV issue column marks duplicate on both DEV-A01 00:30 rows."""
        rows = _load_csv_rows()
        half_hour = [
            r
            for r in rows
            if r["device_id"] == "DEV-A01" and r["reading_at"] == "2024-01-01T00:30:00Z"
        ]
        assert len(half_hour) == 2
        assert all(r["issue"] == "duplicate" for r in half_hour)

    def test_m3_csv_delta_b01(self):
        """CSV issue column marks impossible_delta on DEV-B01 00:15 row."""
        rows = _load_csv_rows()
        row = next(
            r for r in rows if r["device_id"] == "DEV-B01" and r["reading_at"] == "2024-01-01T00:15:00Z"
        )
        assert row["issue"] == "impossible_delta"

    def test_m3_json_schema(self):
        """JSON exposes required top-level keys and MTR-2024-Q1 meter_id."""
        doc = _load_json()
        assert set(doc.keys()) == {
            "meter_id",
            "gap_events",
            "duplicate_events",
            "impossible_delta_events",
            "cost_by_site",
        }
        assert doc["meter_id"] == BATCH

    def test_m3_csv_row_count(self):
        """CSV carries one row per normalized reading (eight total)."""
        rows = _load_csv_rows()
        assert len(rows) == 8

    def test_m3_csv_columns(self):
        """CSV header matches the documented column contract."""
        rows = _load_csv_rows()
        assert list(rows[0].keys()) == [
            "device_id",
            "reading_at",
            "register_kwh",
            "site_id",
            "rate_cents",
            "issue",
        ]

    def test_m3_csv_issues_match_helper(self):
        """Every CSV issue cell matches helper-derived gap/dup/delta flags."""
        normalized = _load_normalized()
        exp = _compute_expectations(normalized)
        rows = _load_csv_rows()
        for row, src in zip(rows, normalized["readings"], strict=True):
            assert row["device_id"] == src["device_id"]
            assert row["reading_at"] == src["reading_at"]
            expected_issue = _expected_csv_issue(
                src, exp["gap_events"], exp["duplicate_events"], exp["impossible_delta_events"]
            )
            assert row["issue"] == expected_issue

    def test_m3_gap_events_exact(self):
        """gap_events set matches helper output exactly."""
        doc = _load_json()
        exp = _compute_expectations(_load_normalized())
        assert doc["gap_events"] == exp["gap_events"]

    def test_m3_duplicate_events_exact(self):
        """duplicate_events set matches helper output exactly."""
        doc = _load_json()
        exp = _compute_expectations(_load_normalized())
        assert doc["duplicate_events"] == exp["duplicate_events"]

    def test_m3_impossible_delta_set_exact(self):
        """impossible_delta_events matches helper output exactly."""
        doc = _load_json()
        exp = _compute_expectations(_load_normalized())
        assert doc["impossible_delta_events"] == exp["impossible_delta_events"]

    def test_m3_clean_rows_empty_issue(self):
        """Rows without anomalies leave the issue column empty."""
        rows = _load_csv_rows()
        clean = next(r for r in rows if r["device_id"] == "DEV-A01" and r["reading_at"] == "2024-01-01T00:00:00Z")
        assert clean["issue"] == ""

    def test_m3_report_idempotent(self):
        """Repeated report verb emits identical JSON bytes."""
        _run_pipeline()
        first = REPORT_JSON.read_bytes()
        subprocess.run(
            ["/app/bin/meterctl", "reconcile", BATCH],
            check=True,
            capture_output=True,
            timeout=30,
        )
        assert REPORT_JSON.read_bytes() == first

    def test_m3_cost_tracks_normalized_correction(self):
        """SITE-NORTH total changes when corrected registers in normalized.json change."""
        _run_pipeline()
        snapshot = NORMALIZED.read_text(encoding="utf-8")
        baseline = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
        baseline_north = baseline["cost_by_site"]["SITE-NORTH"]
        try:
            normalized = json.loads(snapshot)
            half_hour = [
                r
                for r in normalized["readings"]
                if r["device_id"] == "DEV-A01" and r["reading_at"] == "2024-01-01T00:30:00Z"
            ]
            assert len(half_hour) == 2
            half_hour[0]["corrected_register_kwh"] = float(half_hour[0]["corrected_register_kwh"]) + 1.0
            NORMALIZED.write_text(json.dumps(normalized, separators=(",", ":")), encoding="utf-8")
            _run_report_only()
            doc = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
            exp = _compute_expectations(normalized)
            assert abs(doc["cost_by_site"]["SITE-NORTH"] - exp["cost_by_site"]["SITE-NORTH"]) < TOL
            assert abs(doc["cost_by_site"]["SITE-NORTH"] - baseline_north) > TOL
        finally:
            NORMALIZED.write_text(snapshot, encoding="utf-8")
            _run_report_only()

    def test_m3_gap_minutes_dev_a02(self):
        """DEV-A02 gap event records fifteen missing minutes before 00:30."""
        doc = _load_json()
        gap = doc["gap_events"][0]
        assert gap["gap_minutes"] == 15

    def test_m3_csv_register_matches_normalized(self):
        """CSV register_kwh and site_id mirror normalized.json source rows."""
        normalized = _load_normalized()
        rows = _load_csv_rows()
        for csv_row, src in zip(rows, normalized["readings"], strict=True):
            assert float(csv_row["register_kwh"]) == src["register_kwh"]
            assert csv_row["site_id"] == src["site_id"]
            assert float(csv_row["rate_cents"]) == src["rate_cents"]

    def test_m3_only_one_gap_event(self):
        """Exactly one gap event is emitted for the batch."""
        doc = _load_json()
        assert len(doc["gap_events"]) == 1
        assert doc["gap_events"][0]["device_id"] == "DEV-A02"

    def test_m3_impossible_delta_clears_after_limit_raise(self):
        """Raising max_delta above the observed jump removes the DEV-B01 anomaly only."""
        _run_pipeline()
        snapshot = NORMALIZED.read_text(encoding="utf-8")
        try:
            normalized = json.loads(snapshot)
            row = next(
                r
                for r in normalized["readings"]
                if r["device_id"] == "DEV-B01" and r["reading_at"] == "2024-01-01T00:15:00Z"
            )
            row["max_delta_kwh_per_interval"] = 2.0
            NORMALIZED.write_text(json.dumps(normalized, separators=(",", ":")), encoding="utf-8")
            _run_report_only()
            doc = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
            exp = _compute_expectations(normalized)
            assert not any(
                ev["device_id"] == "DEV-B01" and ev["reading_at"] == "2024-01-01T00:15:00Z"
                for ev in doc["impossible_delta_events"]
            )
            assert doc["impossible_delta_events"] == exp["impossible_delta_events"]
            csv_row = next(
                r
                for r in _load_csv_rows()
                if r["device_id"] == "DEV-B01" and r["reading_at"] == "2024-01-01T00:15:00Z"
            )
            assert csv_row["issue"] == ""
        finally:
            NORMALIZED.write_text(snapshot, encoding="utf-8")
            _run_report_only()

    def test_m3_cost_ignores_raw_register_when_corrected_differs(self):
        """Cost roll-up tracks corrected_register_kwh, not raw register_kwh alone."""
        _run_pipeline()
        snapshot = NORMALIZED.read_text(encoding="utf-8")
        baseline = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
        baseline_north = baseline["cost_by_site"]["SITE-NORTH"]
        try:
            normalized = json.loads(snapshot)
            row = next(
                r
                for r in normalized["readings"]
                if r["device_id"] == "DEV-A01" and r["reading_at"] == "2024-01-01T00:15:00Z"
            )
            row["register_kwh"] = float(row["register_kwh"]) + 50.0
            NORMALIZED.write_text(json.dumps(normalized, separators=(",", ":")), encoding="utf-8")
            _run_report_only()
            doc = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
            assert abs(doc["cost_by_site"]["SITE-NORTH"] - baseline_north) < TOL
        finally:
            NORMALIZED.write_text(snapshot, encoding="utf-8")
            _run_report_only()
