"""Verifier for m7desk parallel ingest stress ledger."""

import hashlib
import json
import re
import subprocess
import tomllib
from pathlib import Path

import pytest

APP = Path("/app")
WORK_ROOT = Path("/tmp/m7desk_stress")
MATRIX = APP / "docs" / "lane_matrix.md"
MANIFEST = APP / "data" / "stress_manifest.toml"
LEDGER_PATH = Path("/tmp/vr_stress_ledger.json")
_BUILT = False
_MATRIX_TOTAL = 32
_SCENARIO_CATALOGS = ("lane_a", "lane_b", "lane_c", "lane_d")
_EXPECTED = {
    "lane_a": 8,
    "lane_b": 8,
    "lane_c": 8,
    "lane_d": 8,
}


@pytest.fixture(scope="session", autouse=True)
def _build_once() -> None:
    global _BUILT
    if _BUILT:
        return
    subprocess.run(["bash", str(APP / "scripts" / "build.sh")], cwd="/app", check=True)
    _BUILT = True


@pytest.fixture(scope="session")
def stress_result() -> subprocess.CompletedProcess[str]:
    """Run the stress harness once per verifier session."""
    if WORK_ROOT.exists():
        import shutil

        shutil.rmtree(WORK_ROOT)
    return subprocess.run(
        [
            str(APP / "bin" / "m7desk"),
            "run-stress",
            "--manifest",
            str(MANIFEST),
            "--output",
            str(LEDGER_PATH),
        ],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="session")
def ledger(stress_result: subprocess.CompletedProcess[str]) -> dict:
    """Parse stress ledger JSON after a successful run."""
    assert stress_result.returncode == 0, stress_result.stderr
    return json.loads(LEDGER_PATH.read_text())


def _lane_entry(ledger: dict, lane_id: str) -> dict:
    for entry in ledger["lanes"]:
        if entry["lane_id"] == lane_id:
            return entry
    raise KeyError(lane_id)


def _sqlite_scalar(db_path: Path, sql: str) -> str:
    proc = subprocess.run(
        ["sqlite3", str(db_path), sql],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _sqlite_rows(db_path: Path, sql: str) -> list[str]:
    proc = subprocess.run(
        ["sqlite3", str(db_path), sql],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in proc.stdout.splitlines() if line]


def _manifest_lane(lane_id: str) -> dict:
    data = tomllib.loads(MANIFEST.read_text())
    for spec in data["lanes"]:
        if spec["lane_id"] == lane_id:
            return spec
    raise KeyError(lane_id)


def _ffprobe_dur_ms(media_path: Path) -> int:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(media_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    seconds = float(proc.stdout.strip())
    return int(round(seconds * 1000.0))


def _recompute_digest_from_file() -> str:
    """Match harness: SHA-256 of on-disk JSON with ledger_digest cleared."""
    raw = LEDGER_PATH.read_text()
    patched = re.sub(
        r'"ledger_digest": "[0-9a-f]{64}"',
        '"ledger_digest": ""',
        raw,
        count=1,
    )
    return hashlib.sha256(patched.encode()).hexdigest()


def test_run_exit_zero(stress_result: subprocess.CompletedProcess[str]) -> None:
    """Stress harness exits zero when catalog contention fixes are applied."""
    assert stress_result.returncode == 0, stress_result.stderr


def test_scn_a_row_total(ledger: dict) -> None:
    """Scenario A catalog retains matrix row total."""
    entry = _lane_entry(ledger, "lane_a")
    assert entry["observed_rows"] == _EXPECTED["lane_a"]
    assert str(_EXPECTED["lane_a"]) in MATRIX.read_text()


def test_scn_b_row_total(ledger: dict) -> None:
    """Scenario B catalog retains matrix row total."""
    entry = _lane_entry(ledger, "lane_b")
    assert entry["observed_rows"] == _EXPECTED["lane_b"]


def test_scn_c_row_total(ledger: dict) -> None:
    """Scenario C catalog retains matrix row total."""
    entry = _lane_entry(ledger, "lane_c")
    assert entry["observed_rows"] == _EXPECTED["lane_c"]


def test_scn_d_row_total(ledger: dict) -> None:
    """Scenario D catalog retains matrix row total."""
    entry = _lane_entry(ledger, "lane_d")
    assert entry["observed_rows"] == _EXPECTED["lane_d"]


def test_scn_a_contention_counter(ledger: dict) -> None:
    """Scenario A records zero busy counter in ledger."""
    entry = _lane_entry(ledger, "lane_a")
    assert entry["busy_events"] == 0


def test_scn_b_contention_counter(ledger: dict) -> None:
    """Scenario B records zero busy counter in ledger."""
    entry = _lane_entry(ledger, "lane_b")
    assert entry["busy_events"] == 0


def test_scn_c_contention_counter(ledger: dict) -> None:
    """Scenario C records zero busy counter in ledger."""
    entry = _lane_entry(ledger, "lane_c")
    assert entry["busy_events"] == 0


def test_scn_d_contention_counter(ledger: dict) -> None:
    """Scenario D records zero busy counter in ledger."""
    entry = _lane_entry(ledger, "lane_d")
    assert entry["busy_events"] == 0


def test_scn_a_db_ok(ledger: dict) -> None:
    """Scenario A sqlite integrity_check passes on work catalog."""
    entry = _lane_entry(ledger, "lane_a")
    assert entry["integrity_ok"] is True
    db = WORK_ROOT / "lane_a.db"
    assert _sqlite_scalar(db, "PRAGMA integrity_check;") == "ok"


def test_scn_b_db_ok(ledger: dict) -> None:
    """Scenario B sqlite integrity_check passes on work catalog."""
    entry = _lane_entry(ledger, "lane_b")
    assert entry["integrity_ok"] is True


def test_scn_a_mode_flag(ledger: dict) -> None:
    """Scenario A ledger journal_mode field matches write-ahead expectation."""
    entry = _lane_entry(ledger, "lane_a")
    assert entry["journal_mode"] == "wal"
    db = WORK_ROOT / "lane_a.db"
    assert _sqlite_scalar(db, "PRAGMA journal_mode;") == "wal"


def test_scn_b_mode_flag(ledger: dict) -> None:
    """Scenario B ledger journal_mode field matches write-ahead expectation."""
    entry = _lane_entry(ledger, "lane_b")
    assert entry["journal_mode"] == "wal"


def test_scn_c_db_ok(ledger: dict) -> None:
    """Scenario C sqlite integrity_check passes on work catalog."""
    entry = _lane_entry(ledger, "lane_c")
    assert entry["integrity_ok"] is True


def test_scn_d_mode_flag(ledger: dict) -> None:
    """Scenario D ledger journal_mode field matches write-ahead expectation."""
    entry = _lane_entry(ledger, "lane_d")
    assert entry["journal_mode"] == "wal"


def test_bundle_all_ok(ledger: dict) -> None:
    """Ledger summary all_complete is true after full matrix pass."""
    assert ledger["summary"]["all_complete"] is True


def test_digest_recompute_match(ledger: dict) -> None:
    """Ledger digest matches ingest_contract hash of pre-final JSON body."""
    digest = ledger["summary"]["ledger_digest"]
    assert re.fullmatch(r"[0-9a-f]{64}", digest)
    assert _recompute_digest_from_file() == digest


def test_grand_total_facts(ledger: dict) -> None:
    """All scenario catalogs together hold matrix grand total fact rows."""
    assert ledger["summary"]["all_complete"] is True
    total = sum(
        int(_sqlite_scalar(WORK_ROOT / f"{cat}.db", "SELECT COUNT(*) FROM facts;"))
        for cat in _SCENARIO_CATALOGS
    )
    assert total == _MATRIX_TOTAL


def test_scn_a_duration_anchor(ledger: dict) -> None:
    """Scenario A anchor clip dur_ms matches ffprobe-derived milliseconds."""
    assert _lane_entry(ledger, "lane_a")["observed_rows"] == _EXPECTED["lane_a"]
    clip = "a01.mp4"
    expected_ms = _ffprobe_dur_ms(APP / "data" / "clips" / clip)
    stored = int(
        _sqlite_scalar(
            WORK_ROOT / "lane_a.db",
            f"SELECT dur_ms FROM facts WHERE clip_key='{clip}';",
        )
    )
    assert stored == expected_ms
    assert 200 <= expected_ms <= 300


def test_scn_c_distinct_hashes(ledger: dict) -> None:
    """Scenario C persists a unique stream_hash per ingested clip body."""
    assert _lane_entry(ledger, "lane_c")["observed_rows"] == _EXPECTED["lane_c"]
    db = WORK_ROOT / "lane_c.db"
    row_total = int(_sqlite_scalar(db, "SELECT COUNT(*) FROM facts;"))
    distinct = int(_sqlite_scalar(db, "SELECT COUNT(DISTINCT stream_hash) FROM facts;"))
    assert row_total == distinct == _EXPECTED["lane_c"]


def test_scn_b_dual_reader_counts(ledger: dict) -> None:
    """Scenario B catalog allows concurrent readers after stress (WAL visibility)."""
    assert _lane_entry(ledger, "lane_b")["journal_mode"] == "wal"
    db = WORK_ROOT / "lane_b.db"
    sql = "SELECT COUNT(*) FROM facts;"
    first = int(_sqlite_scalar(db, sql))
    second = int(
        subprocess.run(
            ["sqlite3", str(db), sql],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )
    assert first == second == _EXPECTED["lane_b"]


def test_scn_d_expected_parity(ledger: dict) -> None:
    """Scenario D ledger expected_rows matches matrix and manifest."""
    entry = _lane_entry(ledger, "lane_d")
    spec = _manifest_lane("lane_d")
    assert entry["expected_rows"] == spec["expected_rows"] == _EXPECTED["lane_d"]


def test_scn_a_counter_db_parity(ledger: dict) -> None:
    """Scenario A ledger busy_events matches meta counter in catalog file."""
    entry = _lane_entry(ledger, "lane_a")
    meta_val = int(
        _sqlite_scalar(
            WORK_ROOT / "lane_a.db",
            "SELECT value FROM meta WHERE key='busy_events';",
        )
    )
    assert entry["busy_events"] == meta_val == 0


def test_scn_a_stored_keys_complete(ledger: dict) -> None:
    """Scenario A fact keys exactly match manifest clip list for that scenario."""
    assert _lane_entry(ledger, "lane_a")["observed_rows"] == _EXPECTED["lane_a"]
    expected = set(_manifest_lane("lane_a")["clips"])
    stored = set(
        _sqlite_rows(
            WORK_ROOT / "lane_a.db",
            "SELECT clip_key FROM facts ORDER BY clip_key;",
        )
    )
    assert stored == expected
    assert len(stored) == 8


def test_repeat_harness_scn_b_rows(ledger: dict) -> None:
    """Second harness invocation still fills scenario B catalog to matrix total."""
    assert _lane_entry(ledger, "lane_b")["observed_rows"] == _EXPECTED["lane_b"]
    if WORK_ROOT.exists():
        import shutil

        shutil.rmtree(WORK_ROOT)
    rerun = subprocess.run(
        [
            str(APP / "bin" / "m7desk"),
            "run-stress",
            "--manifest",
            str(MANIFEST),
            "--output",
            "/tmp/vr_stress_rerun.json",
        ],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert rerun.returncode == 0, rerun.stderr
    got = int(_sqlite_scalar(WORK_ROOT / "lane_b.db", "SELECT COUNT(*) FROM facts;"))
    assert got == _EXPECTED["lane_b"]


def test_harness_stderr_clean(stress_result: subprocess.CompletedProcess[str]) -> None:
    """Successful harness stderr omits database lock errors."""
    assert stress_result.returncode == 0
    assert "database is locked" not in stress_result.stderr.lower()


def test_scn_c_wal_frame_tally(ledger: dict) -> None:
    """Scenario C WAL checkpoint reports zero busy frames after ingest."""
    assert _lane_entry(ledger, "lane_c")["journal_mode"] == "wal"
    raw = _sqlite_scalar(WORK_ROOT / "lane_c.db", "PRAGMA wal_checkpoint;")
    busy_frames = int(raw.split("|")[0])
    assert busy_frames == 0


def test_scn_a_sync_mode_normal(ledger: dict) -> None:
    """Scenario A catalog synchronous pragma is not OFF after K2 NORMAL bundle."""
    assert _lane_entry(ledger, "lane_a")["journal_mode"] == "wal"
    sync = int(_sqlite_scalar(WORK_ROOT / "lane_a.db", "PRAGMA synchronous;"))
    assert sync in (1, 2)


def test_scn_b_journal_family_active(ledger: dict) -> None:
    """Scenario B effective journal family on disk is wal, not delete rollback family."""
    assert _lane_entry(ledger, "lane_b")["observed_rows"] == _EXPECTED["lane_b"]
    on_disk = _sqlite_scalar(WORK_ROOT / "lane_b.db", "PRAGMA journal_mode;")
    assert on_disk == "wal"
    assert on_disk != "delete"
