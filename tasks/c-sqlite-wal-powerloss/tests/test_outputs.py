"""Verifier for embedded catalog crash-suite recovery report."""

import json
import re
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
AUDIT_DIR = Path("/tmp/datalog_audit")
FIELD_MATRIX = APP / "docs" / "field_matrix.md"
_BUILT = False
_VAL_SCALE = 1.70
_EXPECTED_ROWS = {
    "alpha": ("KIT-A", 48),
    "bravo": ("KIT-B", 36),
    "charlie": ("KIT-C", 52),
    "delta": ("KIT-D", 40),
}


@pytest.fixture(scope="session", autouse=True)
def _build_once() -> None:
    """Build datalog once per verifier session."""
    global _BUILT
    if _BUILT:
        return
    subprocess.run(["bash", str(APP / "scripts" / "build.sh")], cwd="/app", check=True)
    _BUILT = True


@pytest.fixture(scope="session")
def audit_result() -> subprocess.CompletedProcess[str]:
    """Run the crash-suite audit command."""
    return subprocess.run(
        [
            "/app/bin/datalog",
            "audit",
            "--output",
            "/app/output/recovery_report.json",
        ],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )


def _sqlite_scalar(db_path: Path, sql: str) -> str:
    proc = subprocess.run(
        ["sqlite3", str(db_path), sql],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _expected_rows() -> dict[str, int]:
    text = FIELD_MATRIX.read_text()
    rows: dict[str, int] = {}
    for sid, (kit, count) in _EXPECTED_ROWS.items():
        assert kit in text
        assert str(count) in text
        rows[sid] = count
    return rows


def _require_audit_ok(audit_result: subprocess.CompletedProcess[str]) -> None:
    assert audit_result.returncode == 0, audit_result.stderr


def _sidecar_size(db_path: Path, suffix: str) -> int:
    sidecar = Path(f"{db_path}{suffix}")
    if not sidecar.is_file():
        return 0
    return sidecar.stat().st_size


def _expected_val_sum(row_total: int) -> float:
    """Triangular sum for val = seq * 1.70 seed contract."""
    return _VAL_SCALE * row_total * (row_total + 1) / 2


def _load_recovery_report() -> dict:
    return json.loads(Path("/app/output/recovery_report.json").read_text())


def _report_scenarios_by_id(report: dict) -> dict[str, dict]:
    return {entry["id"]: entry for entry in report["scenarios"]}


def _audit_digest_hex(scenarios: list[dict]) -> str:
    """Same rolling hash as write_report() in audit_run.c."""
    digest = 5381
    for entry in scenarios:
        digest = ((digest << 5) + digest) + int(entry["recovered"])
        digest = ((digest << 5) + digest) + int(entry["row_count"])
        digest = ((digest << 5) + digest) + int(entry["integrity_ok"])
        digest = ((digest << 5) + digest) + int(entry["schema_marker"])
    return f"{digest & 0xFFFFFFFF:08x}"


def _assert_seq_val_contract(db_path: Path, row_total: int) -> None:
    """Contiguous seq 1..N and val = seq * 1.70 for every reading row."""
    span = int(
        _sqlite_scalar(
            db_path,
            "SELECT MAX(seq) - MIN(seq) + 1 FROM readings;",
        )
    )
    distinct = int(_sqlite_scalar(db_path, "SELECT COUNT(DISTINCT seq) FROM readings;"))
    count = int(_sqlite_scalar(db_path, "SELECT COUNT(*) FROM readings;"))
    assert int(_sqlite_scalar(db_path, "SELECT MIN(seq) FROM readings;")) == 1
    assert int(_sqlite_scalar(db_path, "SELECT MAX(seq) FROM readings;")) == row_total
    assert span == row_total
    assert distinct == row_total
    assert count == row_total
    observed_sum = float(_sqlite_scalar(db_path, "SELECT SUM(val) FROM readings;"))
    assert observed_sum == pytest.approx(_expected_val_sum(row_total), rel=1e-9, abs=1e-6)
    per_row = float(
        _sqlite_scalar(
            db_path,
            "SELECT AVG(val / seq) FROM readings WHERE seq > 0;",
        )
    )
    assert per_row == pytest.approx(_VAL_SCALE, rel=1e-9, abs=1e-6)


def test_audit_exit_success(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Crash-suite audit exits zero when durability fixes are applied."""
    assert audit_result.returncode == 0, audit_result.stderr
    report = json.loads(Path("/app/output/recovery_report.json").read_text())
    assert report["summary"]["all_recovered"] is True


def test_recovery_report_structure(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Recovery report JSON matches storage contract scenario and summary fields."""
    assert audit_result.returncode == 0
    report = json.loads(Path("/app/output/recovery_report.json").read_text())
    assert "scenarios" in report
    assert len(report["scenarios"]) == 4
    for s in report["scenarios"]:
        assert all(
            k in s
            for k in [
                "id",
                "kit",
                "recovered",
                "integrity_ok",
                "row_count",
                "schema_marker",
            ]
        )
        assert s["recovered"] is True
        assert s["integrity_ok"] is True
        assert s["schema_marker"] == 2
    assert report["summary"]["all_recovered"] is True


def test_output_at_instructed_path(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Recovery report is written to the instruction output path."""
    assert audit_result.returncode == 0
    report_path = Path("/app/output/recovery_report.json")
    assert report_path.is_file()
    report = json.loads(report_path.read_text())
    assert report["summary"]["all_recovered"] is True


def test_alpha_catalog_rows(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Alpha kit catalog under audit workdir retains matrix row total."""
    assert audit_result.returncode == 0
    expected = _expected_rows()["alpha"]
    got = int(_sqlite_scalar(AUDIT_DIR / "alpha.db", "SELECT COUNT(*) FROM readings;"))
    assert got == expected


def test_bravo_catalog_rows(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Bravo kit catalog under audit workdir retains matrix row total."""
    assert audit_result.returncode == 0
    expected = _expected_rows()["bravo"]
    got = int(_sqlite_scalar(AUDIT_DIR / "bravo.db", "SELECT COUNT(*) FROM readings;"))
    assert got == expected


def test_charlie_catalog_rows(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Charlie kit catalog under audit workdir retains matrix row total."""
    assert audit_result.returncode == 0
    expected = _expected_rows()["charlie"]
    got = int(_sqlite_scalar(AUDIT_DIR / "charlie.db", "SELECT COUNT(*) FROM readings;"))
    assert got == expected


def test_delta_catalog_rows(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Delta kit catalog under audit workdir retains matrix row total."""
    assert audit_result.returncode == 0
    expected = _expected_rows()["delta"]
    got = int(_sqlite_scalar(AUDIT_DIR / "delta.db", "SELECT COUNT(*) FROM readings;"))
    assert got == expected


def test_alpha_catalog_integrity(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Alpha kit catalog passes sqlite integrity_check after crash suite."""
    assert audit_result.returncode == 0
    assert _sqlite_scalar(AUDIT_DIR / "alpha.db", "PRAGMA integrity_check;") == "ok"


def test_bravo_catalog_row_total(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Bravo kit row total remains readable from the on-disk catalog file."""
    assert audit_result.returncode == 0
    assert int(_sqlite_scalar(AUDIT_DIR / "bravo.db", "SELECT COUNT(*) FROM readings;")) == _expected_rows()["bravo"]


def test_charlie_catalog_integrity(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Charlie kit catalog passes sqlite integrity_check after crash suite."""
    assert audit_result.returncode == 0
    assert _sqlite_scalar(AUDIT_DIR / "charlie.db", "PRAGMA integrity_check;") == "ok"


def test_delta_catalog_integrity(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Delta kit catalog passes sqlite integrity_check after crash suite."""
    assert audit_result.returncode == 0
    assert _sqlite_scalar(AUDIT_DIR / "delta.db", "PRAGMA integrity_check;") == "ok"


def test_schema_marker_from_catalog(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Each audit catalog carries schema marker 2 from storage contract."""
    assert audit_result.returncode == 0
    for sid in _EXPECTED_ROWS:
        marker = int(
            _sqlite_scalar(
                AUDIT_DIR / f"{sid}.db",
                "SELECT value FROM meta WHERE key='schema_marker';",
            )
        )
        assert marker == 2


def test_delta_kit_label(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Delta kit rows retain the KIT-D label after crash suite."""
    assert audit_result.returncode == 0
    label = _sqlite_scalar(
        AUDIT_DIR / "delta.db",
        "SELECT DISTINCT kit FROM readings LIMIT 1;",
    )
    assert label == "KIT-D"


def test_cycle_sync_marker_present(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Audit workdir records cycle sync marker after successful maintenance."""
    assert audit_result.returncode == 0
    assert (AUDIT_DIR / ".cycle_sync_marker").is_file()


def test_field_matrix_grounded() -> None:
    """Field matrix documents kit labels and row totals used by verifier."""
    _expected_rows()


def test_alpha_sync_full_on_reopen(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Every reopened catalog reports synchronous FULL (numeric 2) per storage contract."""
    _require_audit_ok(audit_result)
    for sid in _EXPECTED_ROWS:
        sync_level = int(_sqlite_scalar(AUDIT_DIR / f"{sid}.db", "PRAGMA synchronous;"))
        assert sync_level == 2


def test_all_catalogs_journal_mode_wal(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Each scenario catalog stays on write-ahead journal mode after crash recovery."""
    _require_audit_ok(audit_result)
    for sid in _EXPECTED_ROWS:
        mode = _sqlite_scalar(AUDIT_DIR / f"{sid}.db", "PRAGMA journal_mode;").lower()
        assert mode == "wal"


def test_bravo_seq_integrity_chain(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Bravo readings keep a gap-free seq chain from 1 through the matrix row total."""
    _require_audit_ok(audit_result)
    db = AUDIT_DIR / "bravo.db"
    row_total = _expected_rows()["bravo"]
    span = int(
        _sqlite_scalar(
            db,
            "SELECT MAX(seq) - MIN(seq) + 1 FROM readings;",
        )
    )
    distinct = int(_sqlite_scalar(db, "SELECT COUNT(DISTINCT seq) FROM readings;"))
    minimum = int(_sqlite_scalar(db, "SELECT MIN(seq) FROM readings;"))
    maximum = int(_sqlite_scalar(db, "SELECT MAX(seq) FROM readings;"))
    count = int(_sqlite_scalar(db, "SELECT COUNT(*) FROM readings;"))
    assert minimum == 1
    assert maximum == row_total
    assert span == row_total
    assert distinct == row_total
    assert count == row_total


def test_charlie_wal_sidecar_absent(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Charlie main catalog drops the -wal sidecar after successful consolidation."""
    _require_audit_ok(audit_result)
    assert _sidecar_size(AUDIT_DIR / "charlie.db", "-wal") == 0


def test_delta_probe_sidecar_absent(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Delta probe catalog from the maintenance probe carries no -wal sidecar bytes."""
    _require_audit_ok(audit_result)
    sid = "delta"
    assert _sidecar_size(AUDIT_DIR / f"{sid}_probe.db", "-wal") == 0


def test_charlie_readings_val_aggregate(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Charlie val column sum matches seq * 1.70 seed contract across all rows."""
    _require_audit_ok(audit_result)
    row_total = _expected_rows()["charlie"]
    observed = float(_sqlite_scalar(AUDIT_DIR / "charlie.db", "SELECT SUM(val) FROM readings;"))
    assert observed == pytest.approx(_expected_val_sum(row_total), rel=1e-9, abs=1e-6)
    per_row = float(
        _sqlite_scalar(
            AUDIT_DIR / "charlie.db",
            "SELECT AVG(val / seq) FROM readings WHERE seq > 0;",
        )
    )
    assert per_row == pytest.approx(_VAL_SCALE, rel=1e-9, abs=1e-6)


def test_charlie_shm_sidecar_absent(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Charlie main catalog drops the -shm sidecar after successful consolidation."""
    _require_audit_ok(audit_result)
    assert _sidecar_size(AUDIT_DIR / "charlie.db", "-shm") == 0


def test_cycle_sync_marker_nonempty(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Cycle sync marker under the audit workdir contains at least one byte."""
    _require_audit_ok(audit_result)
    marker = AUDIT_DIR / ".cycle_sync_marker"
    assert marker.is_file()
    assert marker.stat().st_size >= 1


def test_meta_schema_marker_exclusive(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Meta table holds exactly one schema_marker row with contract value 2."""
    _require_audit_ok(audit_result)
    for sid in _EXPECTED_ROWS:
        db = AUDIT_DIR / f"{sid}.db"
        marker_rows = int(
            _sqlite_scalar(db, "SELECT COUNT(*) FROM meta WHERE key='schema_marker';")
        )
        marker_val = int(
            _sqlite_scalar(db, "SELECT value FROM meta WHERE key='schema_marker';")
        )
        meta_rows = int(_sqlite_scalar(db, "SELECT COUNT(*) FROM meta;"))
        assert marker_rows == 1
        assert marker_val == 2
        assert meta_rows >= 1


def test_delta_max_seq_matches_matrix(audit_result: subprocess.CompletedProcess[str]) -> None:
    """Delta kit highest seq equals the matrix row total and matches row count."""
    _require_audit_ok(audit_result)
    row_total = _expected_rows()["delta"]
    db = AUDIT_DIR / "delta.db"
    max_seq = int(_sqlite_scalar(db, "SELECT MAX(seq) FROM readings;"))
    row_count = int(_sqlite_scalar(db, "SELECT COUNT(*) FROM readings;"))
    assert max_seq == row_total
    assert row_count == row_total
    assert int(_sqlite_scalar(db, "SELECT COUNT(*) FROM readings WHERE seq > 0;")) == row_total


def test_recovery_report_row_counts_match_disk_catalogs(
    audit_result: subprocess.CompletedProcess[str],
) -> None:
    """Each scenario row_count in the JSON report matches matrix and on-disk COUNT."""
    _require_audit_ok(audit_result)
    matrix = _expected_rows()
    by_id = _report_scenarios_by_id(_load_recovery_report())
    assert set(by_id) == set(_EXPECTED_ROWS)
    for sid, expected_count in matrix.items():
        entry = by_id[sid]
        on_disk = int(
            _sqlite_scalar(AUDIT_DIR / f"{sid}.db", "SELECT COUNT(*) FROM readings;")
        )
        assert entry["row_count"] == expected_count
        assert on_disk == expected_count
        assert entry["row_count"] == on_disk


def test_recovery_report_kit_labels_match_readings(
    audit_result: subprocess.CompletedProcess[str],
) -> None:
    """Report kit labels match field matrix and DISTINCT kit values in each catalog."""
    _require_audit_ok(audit_result)
    by_id = _report_scenarios_by_id(_load_recovery_report())
    for sid, (kit, row_total) in _EXPECTED_ROWS.items():
        entry = by_id[sid]
        db = AUDIT_DIR / f"{sid}.db"
        assert entry["kit"] == kit
        distinct_kits = int(
            _sqlite_scalar(db, "SELECT COUNT(DISTINCT kit) FROM readings;")
        )
        label = _sqlite_scalar(db, "SELECT DISTINCT kit FROM readings LIMIT 1;")
        assert distinct_kits == 1
        assert label == kit
        assert entry["row_count"] == row_total


def test_audit_digest_matches_scenario_outcomes(
    audit_result: subprocess.CompletedProcess[str],
) -> None:
    """summary.audit_digest is an 8-hex digest consistent with scenario outcomes."""
    _require_audit_ok(audit_result)
    report = _load_recovery_report()
    digest = report["summary"]["audit_digest"]
    assert re.fullmatch(r"[0-9a-f]{8}", digest)
    assert digest == _audit_digest_hex(report["scenarios"])
    for entry in report["scenarios"]:
        assert entry["recovered"] is True
        assert entry["integrity_ok"] is True


def test_alpha_and_delta_seq_val_contract(
    audit_result: subprocess.CompletedProcess[str],
) -> None:
    """Alpha and delta catalogs both satisfy contiguous seq and val=seq*1.70."""
    _require_audit_ok(audit_result)
    for sid in ("alpha", "delta"):
        row_total = _expected_rows()[sid]
        _assert_seq_val_contract(AUDIT_DIR / f"{sid}.db", row_total)


def test_all_probe_catalogs_sidecar_clean(
    audit_result: subprocess.CompletedProcess[str],
) -> None:
    """Every maintenance probe catalog under the audit workdir has no wal/shm bytes."""
    _require_audit_ok(audit_result)
    for sid in _EXPECTED_ROWS:
        probe = AUDIT_DIR / f"{sid}_probe.db"
        assert probe.is_file()
        assert _sidecar_size(probe, "-wal") == 0
        assert _sidecar_size(probe, "-shm") == 0
        assert _sqlite_scalar(probe, "PRAGMA integrity_check;") == "ok"
