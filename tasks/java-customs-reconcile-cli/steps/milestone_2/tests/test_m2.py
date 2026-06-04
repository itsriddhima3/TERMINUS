"""Milestone 2 — tariff API enrichment (live fixture cross-checks)."""

import json
import subprocess
import time
import urllib.request
from pathlib import Path

ENRICHED = Path("/app/var/enriched.json")
BATCH = "SHIP-2024-Q1"
API = "http://127.0.0.1:3921"

FX = {"USD": 1.0, "EUR": 1.1, "GBP": 1.25, "JPY": 0.0067}
TARIFF = {
    "8471300000": 5.0,
    "2204210000": 8.0,
    "6109100000": 6.0,
    "1604140000": 4.0,
}
QUOTA = {
    "8471300000": False,
    "2204210000": False,
    "6109100000": True,
    "1604140000": False,
}
SHIP_KEYS = {
    "line_id",
    "importer_id",
    "hs10",
    "currency",
    "declared_value",
    "declared_duty",
}
ENRICH_KEYS = SHIP_KEYS | {
    "tariff_pct",
    "fx_to_usd",
    "quota_blocked",
    "classification_missing",
}


def _api_json(path: str) -> dict:
    raw = urllib.request.urlopen(f"{API}{path}", timeout=5).read()
    return json.loads(raw)


def _ensure_api():
    try:
        urllib.request.urlopen(f"{API}/health", timeout=1).read()
        return
    except Exception:
        pass
    subprocess.run(["/app/scripts/start-api.sh"], check=False, capture_output=True)
    deadline = time.time() + 5.0
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{API}/health", timeout=1).read()
            return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError("api not reachable")


def _run_ingest_enrich():
    _ensure_api()
    subprocess.run(
        ["/app/bin/customsctl", "ingest", BATCH],
        check=True,
        capture_output=True,
        timeout=30,
    )
    subprocess.run(
        ["/app/bin/customsctl", "enrich", BATCH],
        check=True,
        capture_output=True,
        timeout=30,
    )


def _load() -> dict:
    if not ENRICHED.is_file():
        _run_ingest_enrich()
    return json.loads(ENRICHED.read_text(encoding="utf-8"))


def _row(doc: dict, line_id: str) -> dict:
    return next(r for r in doc["lines"] if r["line_id"] == line_id)


def _live_expectations(line: dict) -> dict:
    hs10 = line["hs10"]
    ccy = line["currency"]
    out = {
        "classification_missing": False,
        "tariff_pct": None,
        "quota_blocked": None,
        "fx_to_usd": None,
    }
    try:
        tariff = _api_json(f"/api/v1/tariff/{hs10}")
        out["tariff_pct"] = float(tariff["rate_pct"])
        quota = _api_json(f"/api/v1/quota/{hs10}")
        out["quota_blocked"] = bool(quota["blocked"])
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            out["classification_missing"] = True
        else:
            raise
    fx = _api_json(f"/api/v1/fx/{ccy}")
    out["fx_to_usd"] = float(fx["fx_to_usd"])
    return out


class TestMilestone2:
    def test_m2_enriched_tariff_l001(self):
        """L001 tariff_pct is 5.0 for hs10 8471300000."""
        doc = _load()
        row = _row(doc, "L001")
        assert row["hs10"] == "8471300000"
        assert row["tariff_pct"] == 5.0

    def test_m2_live_tariff_matches_api(self):
        """Classified lines copy live tariff rate_pct from the service."""
        doc = _load()
        for line_id in ("L001", "L002", "L004", "L005", "L006"):
            row = _row(doc, line_id)
            live = _live_expectations(row)
            assert row["classification_missing"] is False
            assert row["tariff_pct"] == live["tariff_pct"] == TARIFF[row["hs10"]]

    def test_m2_quota_flag_l003(self):
        """L003 is missing classification (no tariff row)."""
        doc = _load()
        row = _row(doc, "L003")
        assert row["classification_missing"] is True
        assert row.get("tariff_pct") is None
        assert row.get("quota_blocked") is None

    def test_m2_fx_eur_factor(self):
        """L002 fx_to_usd matches EUR multiplier 1.1 (not reciprocal)."""
        doc = _load()
        row = _row(doc, "L002")
        assert row["currency"] == "EUR"
        assert abs(row["fx_to_usd"] - FX["EUR"]) < 1e-9
        assert row["fx_to_usd"] > 1.0

    def test_m2_live_fx_matches_api_all_lines(self):
        """Every line fx_to_usd equals the live FX endpoint for its currency."""
        doc = _load()
        for row in doc["lines"]:
            live = _live_expectations(row)
            assert abs(row["fx_to_usd"] - live["fx_to_usd"]) < 1e-9

    def test_m2_live_quota_matches_api(self):
        """Quota flags for classified hs10 codes match live quota endpoint."""
        doc = _load()
        for line_id in ("L001", "L002", "L004", "L005", "L006"):
            row = _row(doc, line_id)
            live = _live_expectations(row)
            assert row["quota_blocked"] == live["quota_blocked"] == QUOTA[row["hs10"]]

    def test_m2_l004_quota_blocked(self):
        """L004 quota_blocked is true for hs10 6109100000."""
        doc = _load()
        assert _row(doc, "L004")["quota_blocked"] is True

    def test_m2_only_l003_missing_classification(self):
        """Exactly one line is flagged classification_missing."""
        doc = _load()
        missing = [r["line_id"] for r in doc["lines"] if r["classification_missing"]]
        assert missing == ["L003"]

    def test_m2_l006_shares_l001_tariff(self):
        """Duplicate hs10 8471300000 on L006 picks up the same tariff_pct as L001."""
        doc = _load()
        assert _row(doc, "L001")["tariff_pct"] == _row(doc, "L006")["tariff_pct"] == 5.0

    def test_m2_enriched_preserves_shipment_fields(self):
        """Enrichment must not mutate ingest columns."""
        _ensure_api()
        ship = json.loads(Path("/app/var/shipments.json").read_text(encoding="utf-8"))
        _run_ingest_enrich()
        doc = _load()
        for ship_row, enrich_row in zip(ship["lines"], doc["lines"], strict=True):
            for key in SHIP_KEYS:
                assert enrich_row[key] == ship_row[key]

    def test_m2_enriched_row_schema(self):
        """Rows include enrichment keys with consistent typing."""
        doc = _load()
        for row in doc["lines"]:
            assert set(row.keys()) == ENRICH_KEYS
            assert isinstance(row["classification_missing"], bool)
            if row["classification_missing"]:
                assert row["tariff_pct"] is None
            else:
                assert isinstance(row["tariff_pct"], (int, float))
                assert isinstance(row["quota_blocked"], bool)
            assert isinstance(row["fx_to_usd"], (int, float))

    def test_m2_enrich_idempotent(self):
        """Two enrich runs produce identical JSON bytes."""
        _run_ingest_enrich()
        first = ENRICHED.read_bytes()
        subprocess.run(
            ["/app/bin/customsctl", "enrich", BATCH],
            check=True,
            capture_output=True,
            timeout=30,
        )
        assert ENRICHED.read_bytes() == first

    def test_m2_line_count_and_order_preserved(self):
        """Enriched artifact retains six lines in catalog order."""
        doc = _load()
        assert [r["line_id"] for r in doc["lines"]] == [
            "L001",
            "L002",
            "L003",
            "L004",
            "L005",
            "L006",
        ]

    def test_m2_l003_fx_present_while_missing_tariff(self):
        """Missing classification still records GBP fx_to_usd from the service."""
        doc = _load()
        row = _row(doc, "L003")
        assert row["classification_missing"] is True
        assert abs(row["fx_to_usd"] - FX["GBP"]) < 1e-9

    def test_m2_l005_jpy_classified_enrichment_complete(self):
        """L005 carries live tariff, FX, and quota fields for classified JPY row."""
        doc = _load()
        row = _row(doc, "L005")
        live = _live_expectations(row)
        assert row["classification_missing"] is False
        assert row["tariff_pct"] == live["tariff_pct"] == TARIFF["1604140000"]
        assert abs(row["fx_to_usd"] - FX["JPY"]) < 1e-9
        assert row["quota_blocked"] is False

    def test_m2_l003_null_tariff_and_quota_when_missing(self):
        """Missing classification leaves tariff_pct and quota_blocked as JSON null."""
        doc = _load()
        row = _row(doc, "L003")
        assert row["classification_missing"] is True
        assert row["tariff_pct"] is None
        assert row["quota_blocked"] is None
        assert abs(row["fx_to_usd"] - FX["GBP"]) < 1e-9

    def test_m2_gbp_fx_not_inverted_reciprocal(self):
        """GBP fx_to_usd uses the multiplier table (>1), not a reciprocal (<1)."""
        doc = _load()
        row = _row(doc, "L003")
        assert row["fx_to_usd"] > 1.0
        assert abs(row["fx_to_usd"] - (1.0 / FX["GBP"])) > 0.1
