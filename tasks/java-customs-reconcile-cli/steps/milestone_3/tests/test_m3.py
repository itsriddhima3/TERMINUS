"""Milestone 3 — reconciliation reports (policy-aware duty gaps + CSV/JSON coupling)."""

import csv
import json
import re
import subprocess
import time
import urllib.request
from pathlib import Path

RECON_JSON = Path("/app/output/reconcile.json")
RECON_CSV = Path("/app/output/reconcile.csv")
ENRICHED = Path("/app/var/enriched.json")
POLICY = Path("/app/config/bench_policy.toml")
BATCH = "SHIP-2024-Q1"
TOL = 0.01

FX = {"USD": 1.0, "EUR": 1.1, "GBP": 1.25, "JPY": 0.0067}
TARIFF = {
    "8471300000": 5.0,
    "2204210000": 8.0,
    "6109100000": 6.0,
    "1604140000": 4.0,
}
IMPORTERS = {
    "L001": "IMP-ALPHA",
    "L002": "IMP-ALPHA",
    "L003": "IMP-BETA",
    "L004": "IMP-BETA",
    "L005": "IMP-GAMMA",
    "L006": "IMP-GAMMA",
}


def _read_policy() -> dict[str, float]:
    body = POLICY.read_text(encoding="utf-8")
    uplift = float(re.search(r"^quota_uplift_multiplier\s*=\s*([0-9.]+)", body, re.M).group(1))
    missing = float(
        re.search(r"^missing_classification_exposure_usd\s*=\s*([0-9.]+)", body, re.M).group(1)
    )
    jpy_scale = float(re.search(r"^\s*scale\s*=\s*([0-9.]+)", body, re.M).group(1))
    return {"quota_uplift": uplift, "missing_usd": missing, "jpy_scale": jpy_scale}


def _value_basis(value: float, ccy: str, policy: dict[str, float]) -> float:
    if ccy.upper() == "JPY":
        return value * policy["jpy_scale"]
    return value


def _expected_duty(row: dict, policy: dict[str, float]) -> float | None:
    """Expected USD duty from enriched row fields and bench policy."""
    if row.get("classification_missing"):
        return None
    tariff = row.get("tariff_pct")
    if tariff is None:
        return None
    hs10 = row["hs10"]
    rate = float(tariff) if tariff is not None else TARIFF.get(hs10)
    if rate is None:
        return None
    basis = _value_basis(float(row["declared_value"]), row["currency"], policy)
    fx = float(row["fx_to_usd"])
    core = basis * fx * (rate / 100.0)
    if row.get("quota_blocked"):
        core *= policy["quota_uplift"]
    return core


def _compute_expectations() -> dict:
    """Derive underpaid/missing/exposure from enriched fixture + bench policy."""
    policy = _read_policy()
    enriched = json.loads(ENRICHED.read_text(encoding="utf-8"))
    underpaid: list[str] = []
    missing: list[str] = []
    line_gaps: dict[str, float] = {}
    exposure: dict[str, float] = {}

    for row in enriched["lines"]:
        lid = row["line_id"]
        imp = row["importer_id"]
        if row["classification_missing"]:
            missing.append(lid)
            exposure[imp] = round(exposure.get(imp, 0.0) + policy["missing_usd"], 6)
            continue
        decl = float(row["declared_duty"])
        expected = _expected_duty(row, policy)
        assert expected is not None
        if decl + TOL < expected:
            underpaid.append(lid)
            gap = round(expected - decl, 6)
            line_gaps[lid] = gap
            exposure[imp] = round(exposure.get(imp, 0.0) + gap, 6)

    return {
        "underpaid_lines": underpaid,
        "missing_classifications": missing,
        "exposure_by_importer": exposure,
        "line_gaps": line_gaps,
        "policy": policy,
    }


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


def _run_pipeline():
    _ensure_api()
    for cmd in ("ingest", "enrich", "reconcile"):
        subprocess.run(
            ["/app/bin/customsctl", cmd, BATCH],
            check=True,
            capture_output=True,
            timeout=30,
        )


def _run_reconcile_only():
    _ensure_api()
    subprocess.run(
        ["/app/bin/customsctl", "reconcile", BATCH],
        check=True,
        capture_output=True,
        timeout=30,
    )


def _write_enriched(doc: dict) -> None:
    """Persist enriched.json in the compact shape customsctl JsonKit can read."""
    ENRICHED.write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")


def _load_json() -> dict:
    if not RECON_JSON.is_file() or not ENRICHED.is_file():
        _run_pipeline()
    return json.loads(RECON_JSON.read_text(encoding="utf-8"))


def _load_csv_rows() -> list[dict]:
    if not RECON_CSV.is_file():
        _run_pipeline()
    return list(csv.DictReader(RECON_CSV.read_text(encoding="utf-8").splitlines()))


class TestMilestone3:
    def test_m3_underpaid_l004(self):
        """L004 is listed as underpaid."""
        doc = _load_json()
        assert "L004" in doc["underpaid_lines"]

    def test_m3_missing_classification_l003(self):
        """L003 is listed as missing classification."""
        doc = _load_json()
        assert "L003" in doc["missing_classifications"]

    def test_m3_importer_exposure_alpha(self):
        """IMP-ALPHA roll-up matches policy-aware gap sum for that importer."""
        doc = _load_json()
        exp = _compute_expectations()
        assert doc["exposure_by_importer"]["IMP-ALPHA"] == exp["exposure_by_importer"]["IMP-ALPHA"]

    def test_m3_importer_exposure_beta(self):
        """IMP-BETA roll-up includes underpaid gaps plus missing-classification bench."""
        doc = _load_json()
        exp = _compute_expectations()
        assert doc["exposure_by_importer"]["IMP-BETA"] == exp["exposure_by_importer"]["IMP-BETA"]

    def test_m3_underpaid_set_exact(self):
        """Underpaid lines are exactly L002 and L004 (no false positives)."""
        doc = _load_json()
        exp = _compute_expectations()
        assert sorted(doc["underpaid_lines"]) == sorted(exp["underpaid_lines"])
        assert set(doc["underpaid_lines"]) == {"L002", "L004"}

    def test_m3_missing_set_exact(self):
        """Missing classification list is exactly L003."""
        doc = _load_json()
        exp = _compute_expectations()
        assert doc["missing_classifications"] == exp["missing_classifications"] == ["L003"]

    def test_m3_exposure_by_importer_exact(self):
        """Importer roll-ups match policy-aware gaps and missing bench."""
        doc = _load_json()
        exp = _compute_expectations()
        assert doc["exposure_by_importer"] == exp["exposure_by_importer"]

    def test_m3_l002_gap_matches_policy_formula(self):
        """L002 CSV exposure matches policy-aware gap from enriched inputs."""
        exp = _compute_expectations()
        rows = _load_csv_rows()
        l2 = next(r for r in rows if r["line_id"] == "L002")
        assert float(l2["exposure_usd"]) == exp["line_gaps"]["L002"]

    def test_m3_l004_gap_matches_quota_uplift_formula(self):
        """L004 CSV exposure matches quota-uplift gap from enriched inputs."""
        exp = _compute_expectations()
        rows = _load_csv_rows()
        l4 = next(r for r in rows if r["line_id"] == "L004")
        assert float(l4["exposure_usd"]) == exp["line_gaps"]["L004"]

    def test_m3_quota_uplift_applied_l004(self):
        """L004 reconcile output reflects quota-blocked uplift, not a static gap."""
        doc = _load_json()
        assert "L004" in doc["underpaid_lines"]
        exp = _compute_expectations()
        rows = _load_csv_rows()
        l4 = next(r for r in rows if r["line_id"] == "L004")
        assert float(l4["exposure_usd"]) == exp["line_gaps"]["L004"]

    def test_m3_missing_bench_from_policy(self):
        """L003 missing-classification CSV exposure comes from bench policy."""
        rows = _load_csv_rows()
        l3 = next(r for r in rows if r["line_id"] == "L003")
        policy = _read_policy()
        assert float(l3["exposure_usd"]) == policy["missing_usd"]

    def test_m3_overpaid_lines_excluded(self):
        """Overpaid or even lines must not appear as underpaid."""
        doc = _load_json()
        under = set(doc["underpaid_lines"])
        assert "L001" not in under
        assert "L005" not in under
        assert "L006" not in under

    def test_m3_csv_row_count(self):
        """CSV has one row per finding (two underpaid + one missing)."""
        rows = _load_csv_rows()
        assert len(rows) == 3
        assert {r["issue"] for r in rows} == {"underpaid", "missing"}

    def test_m3_csv_json_bijection(self):
        """CSV rows match JSON finding sets and per-line exposure amounts."""
        doc = _load_json()
        exp = _compute_expectations()
        rows = _load_csv_rows()
        csv_under = {r["line_id"]: r for r in rows if r["issue"] == "underpaid"}
        csv_missing = {r["line_id"]: r for r in rows if r["issue"] == "missing"}

        assert set(csv_under) == set(doc["underpaid_lines"])
        assert set(csv_missing) == set(doc["missing_classifications"])

        for lid, row in csv_under.items():
            assert row["importer_id"] == IMPORTERS[lid]
            assert float(row["exposure_usd"]) == exp["line_gaps"][lid]

        l3 = csv_missing["L003"]
        assert l3["importer_id"] == "IMP-BETA"
        assert float(l3["exposure_usd"]) == exp["policy"]["missing_usd"]

    def test_m3_csv_l004_underpaid_row(self):
        """CSV row for L004 records underpaid issue with computed exposure."""
        exp = _compute_expectations()
        rows = _load_csv_rows()
        l4 = next(r for r in rows if r["line_id"] == "L004")
        assert l4["issue"] == "underpaid"
        assert l4["importer_id"] == "IMP-BETA"
        assert float(l4["exposure_usd"]) == exp["line_gaps"]["L004"]

    def test_m3_reconcile_schema(self):
        """JSON exposes required top-level keys and SHIP-2024-Q1 batch_id."""
        doc = _load_json()
        assert set(doc.keys()) == {
            "batch_id",
            "underpaid_lines",
            "missing_classifications",
            "exposure_by_importer",
        }
        assert doc["batch_id"] == BATCH
        assert isinstance(doc["underpaid_lines"], list)
        assert isinstance(doc["missing_classifications"], list)
        assert isinstance(doc["exposure_by_importer"], dict)

    def test_m3_gamma_not_overexposed(self):
        """IMP-GAMMA has no underpaid exposure entry."""
        doc = _load_json()
        assert "IMP-GAMMA" not in doc["exposure_by_importer"]

    def test_m3_reconcile_idempotent(self):
        """Repeated reconcile emits identical JSON bytes."""
        _run_pipeline()
        first = RECON_JSON.read_bytes()
        subprocess.run(
            ["/app/bin/customsctl", "reconcile", BATCH],
            check=True,
            capture_output=True,
            timeout=30,
        )
        assert RECON_JSON.read_bytes() == first

    def test_m3_total_exposure_matches_line_gaps(self):
        """Importer roll-up sum matches underpaid gaps plus missing bench."""
        doc = _load_json()
        exp = _compute_expectations()
        total_importers = round(sum(doc["exposure_by_importer"].values()), 6)
        total_lines = round(sum(exp["line_gaps"].values()), 6)
        missing_bench = exp["policy"]["missing_usd"]
        assert total_importers == round(total_lines + missing_bench, 6)
        assert doc["exposure_by_importer"] == exp["exposure_by_importer"]

    def test_m3_exposure_tracks_enriched_declared_value(self):
        """IMP-ALPHA roll-up changes when L002 declared_value in enriched.json changes."""
        _run_pipeline()
        snapshot = ENRICHED.read_text(encoding="utf-8")
        baseline_doc = json.loads(RECON_JSON.read_text(encoding="utf-8"))
        baseline_alpha = baseline_doc["exposure_by_importer"]["IMP-ALPHA"]
        try:
            enriched = json.loads(snapshot)
            for row in enriched["lines"]:
                if row["line_id"] == "L002":
                    row["declared_value"] = float(row["declared_value"]) + 5000.0
                    break
            else:
                raise AssertionError("L002 missing from enriched fixture")
            _write_enriched(enriched)
            _run_reconcile_only()
            doc = json.loads(RECON_JSON.read_text(encoding="utf-8"))
            exp = _compute_expectations()
            mutated_alpha = doc["exposure_by_importer"]["IMP-ALPHA"]
            expected_alpha = exp["exposure_by_importer"]["IMP-ALPHA"]
            assert abs(mutated_alpha - expected_alpha) <= TOL
            assert abs(mutated_alpha - baseline_alpha) > TOL
        finally:
            ENRICHED.write_text(snapshot, encoding="utf-8")
            _run_reconcile_only()

    def test_m3_underpaid_tolerance_inside_band_excludes_line(self):
        """Declared duty within tolerance of expected duty must not be underpaid."""
        _run_pipeline()
        snapshot = ENRICHED.read_text(encoding="utf-8")
        try:
            enriched = json.loads(snapshot)
            row = next(r for r in enriched["lines"] if r["line_id"] == "L002")
            policy = _read_policy()
            expected = _expected_duty(row, policy)
            assert expected is not None
            row["declared_duty"] = round(expected - 0.005, 6)
            _write_enriched(enriched)
            _run_reconcile_only()
            doc = json.loads(RECON_JSON.read_text(encoding="utf-8"))
            assert "L002" not in doc["underpaid_lines"]
            assert doc["exposure_by_importer"].get("IMP-ALPHA", 0.0) == 0.0
        finally:
            ENRICHED.write_text(snapshot, encoding="utf-8")
            _run_reconcile_only()

    def test_m3_underpaid_tolerance_outside_band_includes_line(self):
        """Declared duty below tolerance band must remain underpaid with same gap."""
        _run_pipeline()
        snapshot = ENRICHED.read_text(encoding="utf-8")
        try:
            enriched = json.loads(snapshot)
            row = next(r for r in enriched["lines"] if r["line_id"] == "L002")
            policy = _read_policy()
            expected = _expected_duty(row, policy)
            assert expected is not None
            row["declared_duty"] = round(expected - 0.02, 6)
            _write_enriched(enriched)
            _run_reconcile_only()
            doc = json.loads(RECON_JSON.read_text(encoding="utf-8"))
            exp = _compute_expectations()
            assert "L002" in doc["underpaid_lines"]
            rows = _load_csv_rows()
            l2 = next(r for r in rows if r["line_id"] == "L002")
            gap = float(l2["exposure_usd"])
            assert abs(gap - exp["line_gaps"]["L002"]) <= TOL
            assert abs(gap - 0.02) <= TOL
        finally:
            ENRICHED.write_text(snapshot, encoding="utf-8")
            _run_reconcile_only()

    def test_m3_csv_importer_totals_match_json_rollups(self):
        """Summing CSV exposure_usd by importer matches reconcile.json roll-ups."""
        doc = _load_json()
        rows = _load_csv_rows()
        csv_totals: dict[str, float] = {}
        for row in rows:
            imp = row["importer_id"]
            csv_totals[imp] = round(
                csv_totals.get(imp, 0.0) + float(row["exposure_usd"]), 6
            )
        for imp, total in doc["exposure_by_importer"].items():
            assert abs(csv_totals[imp] - total) <= TOL
        assert set(csv_totals) == set(doc["exposure_by_importer"])

    def test_m3_policy_missing_bench_mutation_updates_l003(self):
        """Changing missing_classification_exposure_usd in bench policy updates L003 CSV."""
        _run_pipeline()
        policy_snapshot = POLICY.read_text(encoding="utf-8")
        try:
            POLICY.write_text(
                policy_snapshot.replace(
                    "missing_classification_exposure_usd = 75.0",
                    "missing_classification_exposure_usd = 100.0",
                ),
                encoding="utf-8",
            )
            _run_reconcile_only()
            rows = _load_csv_rows()
            l3 = next(r for r in rows if r["line_id"] == "L003")
            exp = _compute_expectations()
            assert float(l3["exposure_usd"]) == exp["policy"]["missing_usd"]
            doc = json.loads(RECON_JSON.read_text(encoding="utf-8"))
            assert doc["exposure_by_importer"]["IMP-BETA"] == exp["exposure_by_importer"]["IMP-BETA"]
        finally:
            POLICY.write_text(policy_snapshot, encoding="utf-8")
            _run_reconcile_only()

    def test_m3_disable_quota_block_recomputes_l004_without_uplift(self):
        """Clearing quota_blocked on L004 drops exposure to non-uplift gap (400 USD)."""
        _run_pipeline()
        snapshot = ENRICHED.read_text(encoding="utf-8")
        try:
            enriched = json.loads(snapshot)
            for row in enriched["lines"]:
                if row["line_id"] == "L004":
                    row["quota_blocked"] = False
                    break
            else:
                raise AssertionError("L004 missing from enriched fixture")
            _write_enriched(enriched)
            _run_reconcile_only()
            rows = _load_csv_rows()
            l4 = next(r for r in rows if r["line_id"] == "L004")
            exp = _compute_expectations()
            assert float(l4["exposure_usd"]) == exp["line_gaps"]["L004"]
            doc = json.loads(RECON_JSON.read_text(encoding="utf-8"))
            assert doc["exposure_by_importer"]["IMP-BETA"] == exp["exposure_by_importer"]["IMP-BETA"]
        finally:
            ENRICHED.write_text(snapshot, encoding="utf-8")
            _run_reconcile_only()

    def test_m3_enriched_fx_mutation_recomputes_l002_gap(self):
        """L002 exposure must track enriched fx_to_usd (duty math uses row FX, not 1.0)."""
        _run_pipeline()
        snapshot = ENRICHED.read_text(encoding="utf-8")
        baseline_gap = _compute_expectations()["line_gaps"]["L002"]
        try:
            enriched = json.loads(snapshot)
            row = next(r for r in enriched["lines"] if r["line_id"] == "L002")
            row["fx_to_usd"] = 1.0
            _write_enriched(enriched)
            _run_reconcile_only()
            doc = json.loads(RECON_JSON.read_text(encoding="utf-8"))
            exp = _compute_expectations()
            rows = _load_csv_rows()
            l2 = next(r for r in rows if r["line_id"] == "L002")
            assert "L002" in doc["underpaid_lines"]
            assert abs(float(l2["exposure_usd"]) - exp["line_gaps"]["L002"]) <= TOL
            assert exp["line_gaps"]["L002"] < baseline_gap
        finally:
            ENRICHED.write_text(snapshot, encoding="utf-8")
            _run_reconcile_only()
