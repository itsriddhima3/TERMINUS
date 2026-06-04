"""Milestone 1 — shipment manifest ingest (strict CSV + normalization checks)."""

import csv
import hashlib
import json
import subprocess
import time
import urllib.request
from pathlib import Path

SHIPMENTS = Path("/app/var/shipments.json")
CSV_PATH = Path("/app/data/shipments/SHIP-2024-Q1.csv")
BATCH = "SHIP-2024-Q1"
LINE_ORDER = ["L001", "L002", "L003", "L004", "L005", "L006"]
LINE_KEYS = {"line_id", "importer_id", "hs10", "currency", "declared_value", "declared_duty"}

CCY_ALIASES = {"usd": "USD", "us$": "USD", "eur": "EUR", "gbp": "GBP", "jpy": "JPY"}
HS10_EXPECTED = {
    "L001": "8471300000",
    "L002": "2204210000",
    "L003": "9999999999",
    "L004": "6109100000",
    "L005": "1604140000",
    "L006": "8471300000",
}


def _hs10(raw: str) -> str:
    digits = "".join(c for c in raw if c.isdigit())
    return digits.ljust(10, "0")[:10]


def _ccy(raw: str) -> str:
    return CCY_ALIASES.get(raw.strip().lower(), raw.strip().upper())


def _read_csv_rows() -> list[dict]:
    with CSV_PATH.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _expected_manifest_from_csv() -> dict:
    lines = []
    for row in _read_csv_rows():
        lines.append(
            {
                "line_id": row["line_id"],
                "importer_id": row["importer_id"],
                "hs10": _hs10(row["hs_raw"]),
                "currency": _ccy(row["currency_raw"]),
                "declared_value": float(row["declared_value"]),
                "declared_duty": float(row["declared_duty"]),
            }
        )
    return {"batch_id": BATCH, "lines": lines}


def _ensure_api():
    try:
        urllib.request.urlopen("http://127.0.0.1:3921/health", timeout=1).read()
        return
    except Exception:
        pass
    subprocess.run(["/app/scripts/start-api.sh"], check=False, capture_output=True)
    deadline = time.time() + 5.0
    while time.time() < deadline:
        try:
            urllib.request.urlopen("http://127.0.0.1:3921/health", timeout=1).read()
            return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError("api not reachable")


def _run_ingest() -> subprocess.CompletedProcess:
    _ensure_api()
    return subprocess.run(
        ["/app/bin/customsctl", "ingest", BATCH],
        capture_output=True,
        timeout=30,
    )


def _load() -> dict:
    if not SHIPMENTS.is_file():
        result = _run_ingest()
        assert result.returncode == 0, result.stderr.decode()
    return json.loads(SHIPMENTS.read_text(encoding="utf-8"))


def _canonical_digest(doc: dict) -> str:
    payload = json.dumps(doc, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


class TestMilestone1:
    def test_m1_batch_id_and_line_count(self):
        """Ingest writes batch_id SHIP-2024-Q1 with six lines."""
        doc = _load()
        assert doc["batch_id"] == BATCH
        assert len(doc["lines"]) == 6

    def test_m1_manifest_matches_csv_contract(self):
        """Every persisted line matches CSV-derived hs10, currency, and amounts."""
        doc = _load()
        expected = _expected_manifest_from_csv()
        assert doc["batch_id"] == expected["batch_id"]
        assert len(doc["lines"]) == len(expected["lines"])
        for got, exp in zip(doc["lines"], expected["lines"], strict=True):
            assert got == exp

    def test_m1_line_order_stable(self):
        """Lines appear L001 through L006 in file order (not reversed)."""
        doc = _load()
        assert [r["line_id"] for r in doc["lines"]] == LINE_ORDER

    def test_m1_line_schema_strict(self):
        """Track rows expose only the six contract fields with JSON-safe types."""
        doc = _load()
        for row in doc["lines"]:
            assert set(row.keys()) == LINE_KEYS
            assert isinstance(row["line_id"], str)
            assert isinstance(row["importer_id"], str)
            assert isinstance(row["hs10"], str) and len(row["hs10"]) == 10
            assert isinstance(row["currency"], str) and len(row["currency"]) == 3
            assert isinstance(row["declared_value"], (int, float))
            assert isinstance(row["declared_duty"], (int, float))

    def test_m1_l001_hs10_normalization(self):
        """L001 hs10 is 8471300000 after folding 8471.30.00."""
        doc = _load()
        assert next(r for r in doc["lines"] if r["line_id"] == "L001")["hs10"] == "8471300000"

    def test_m1_l002_currency_alias(self):
        """L002 currency is EUR from lowercase eur."""
        doc = _load()
        assert next(r for r in doc["lines"] if r["line_id"] == "L002")["currency"] == "EUR"

    def test_m1_hs10_table_all_rows(self):
        """Each line_id maps to the bench hs10 table derived from the CSV."""
        doc = _load()
        for row in doc["lines"]:
            assert row["hs10"] == HS10_EXPECTED[row["line_id"]]

    def test_m1_shipments_checksum(self):
        """Canonical manifest digest is stable across reruns."""
        _run_ingest()
        first = _canonical_digest(_load())
        _run_ingest()
        second = _canonical_digest(_load())
        assert first == second
        assert len(first) == 64

    def test_m1_ingest_cli_exit_zero(self):
        """ingest succeeds from a clean slate and writes shipments.json."""
        if SHIPMENTS.exists():
            SHIPMENTS.unlink()
        result = _run_ingest()
        assert result.returncode == 0, result.stderr.decode()
        assert SHIPMENTS.is_file()

    def test_m1_reversed_order_fails_catalog_sequence(self):
        """Reversed ingest cannot satisfy L001-first catalog order."""
        doc = _load()
        ids = [r["line_id"] for r in doc["lines"]]
        assert ids[0] == "L001", "reversed-row trap puts L006 first"
        assert ids[-1] == "L006"

    def test_m1_short_hs_not_six_digit_truncation(self):
        """L006 must not stop at six digits (847130) for 8471.30."""
        doc = _load()
        hs = next(r for r in doc["lines"] if r["line_id"] == "L006")["hs10"]
        assert hs == "8471300000"
        assert hs != "847130"

    def test_m1_importer_ids_preserved(self):
        """Importer identifiers match the CSV manifest."""
        doc = _load()
        expected = {r["line_id"]: r["importer_id"] for r in _expected_manifest_from_csv()["lines"]}
        for row in doc["lines"]:
            assert row["importer_id"] == expected[row["line_id"]]

    def test_m1_declared_values_match_csv(self):
        """Declared value and duty are parsed as floats matching CSV numerics."""
        doc = _load()
        expected = {r["line_id"]: r for r in _expected_manifest_from_csv()["lines"]}
        for row in doc["lines"]:
            exp = expected[row["line_id"]]
            assert row["declared_value"] == exp["declared_value"]
            assert row["declared_duty"] == exp["declared_duty"]

    def test_m1_l005_jpy_currency_iso(self):
        """L005 maps lowercase jpy to ISO JPY (not left as raw token)."""
        doc = _load()
        row = next(r for r in doc["lines"] if r["line_id"] == "L005")
        assert row["currency"] == "JPY"
        assert row["hs10"] == "1604140000"

    def test_m1_l003_unknown_hs_ten_digits(self):
        """L003 unknown HS folds to ten-digit 9999999999 without truncation."""
        doc = _load()
        row = next(r for r in doc["lines"] if r["line_id"] == "L003")
        assert row["hs10"] == "9999999999"
        assert len(row["hs10"]) == 10
        assert row["currency"] == "GBP"
