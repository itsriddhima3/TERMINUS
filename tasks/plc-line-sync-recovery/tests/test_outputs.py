"""Verifier for PLC assembly line sync reconcile report."""

import json
import os
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

import pytest

APP = Path("/app")
ACTIVE = APP / "data" / "active"
FIXTURES = Path("/tests") / "fixtures"
OUT = APP / "output" / "sync_report.json"
GO_BIN = "/usr/local/go/bin/go"
VERIFY_BIN = "/tmp/line_audit_verify_bin"
_BUILT = False


@pytest.fixture(scope="session", autouse=True)
def _build_once() -> None:
    global _BUILT
    if _BUILT:
        return
    subprocess.run(["bash", "/app/scripts/build.sh"], cwd="/app", check=True)
    subprocess.run(["cp", "/app/bin/line_audit", VERIFY_BIN], check=True)
    _BUILT = True


def _digest_hex(
    line_id: str,
    stable_phase: int,
    cycle_chain: int,
    purge: int,
    stale: int,
    stations_live: int,
    lag: str,
    line_synced: bool,
    ttl_drift: int,
) -> str:
    ck = "true" if line_synced else "false"
    got = subprocess.run(
        [
            GO_BIN,
            "run",
            "-mod=mod",
            "/app/tools/digest_cli",
            line_id,
            str(stable_phase),
            str(cycle_chain),
            str(purge),
            str(stale),
            str(stations_live),
            lag,
            ck,
            str(ttl_drift),
        ],
        cwd="/app",
        capture_output=True,
        text=True,
        check=True,
    )
    return got.stdout.strip()


def _crc16(seq: int, payload: str) -> int:
    s = sum(payload.encode()) & 0xFFFFFFFF
    return (s ^ seq) & 0xFFFF


def _ttl_left(seq: int) -> int:
    return 300 - (seq % 50)


def _expected_from_fixture(line_name: str) -> dict:
    line_dir = FIXTURES / line_name
    line_path = line_dir / "assembly_line.json"
    if not line_path.exists():
        line_path = line_dir / "cluster_pack.json"
    pack = json.loads(line_path.read_text())
    line_id = pack.get("line_id", pack.get("pack_id", line_name.removeprefix("line_")))
    q = pack["q_size"]
    split_epoch = pack.get("split_gen", pack.get("split_epoch", 5))
    lag_tight = pack.get("lag_tight_ms", pack.get("drift_tight_ms", 25))
    offsets: dict[str, int] = {}
    freezes: list[int] = []
    rows: list[dict] = []
    stations = pack.get("stations", pack.get("nodes", []))
    for mid in stations:
        meta = json.loads((line_dir / "stations" / mid / "meta.json").read_text())
        offsets[mid] = meta.get("replication_lag_ms", meta["clock_offset_ms"])
        freezes.append(meta.get("commit_watermark", meta.get("cache_watermark", meta["freeze_seq"])))
        seg = line_dir / "stations" / mid / "seg_001.jsonl"
        if not seg.exists():
            continue
        for line in seg.read_text().splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            entry["member"] = mid
            rows.append(entry)
    wm = min(freezes) if freezes else 0
    by_seq: dict[int, list] = defaultdict(list)
    all_rows: dict[int, list] = defaultdict(list)
    for entry in rows:
        all_rows[entry["seq"]].append(entry)
        if entry["seq"] > wm:
            by_seq[entry["seq"]].append(entry)
    accepted: dict[int, int] = {}
    purge = 0
    stale = 0
    live: set[str] = set()
    line_synced = True
    ttl_drift = 0
    for seq in sorted(by_seq):
        buckets: dict[tuple, list] = defaultdict(list)
        for entry in by_seq[seq]:
            buckets[(entry["epoch"], entry["payload"])].append(entry)
        picked = None
        best_adj = None
        for key, items in buckets.items():
            if len({it["member"] for it in items}) < q:
                continue
            valid = [it for it in items if _crc16(it["seq"], it["payload"]) == it["crc"]]
            if len(valid) < q:
                continue
            adj = min(it["wall_ms"] - offsets[it["member"]] for it in valid)
            if picked is None or adj < best_adj:
                picked, best_adj = key, adj
        if picked is None:
            stale += 1
            continue
        items = buckets[picked]
        purge += sum(1 for it in items if _crc16(it["seq"], it["payload"]) != it["crc"])
        epoch = picked[0]
        valid = [it for it in items if _crc16(it["seq"], it["payload"]) == it["crc"]]
        ttls = [_ttl_left(it["seq"]) for it in valid]
        if ttls:
            spread = max(ttls) - min(ttls)
            if spread > ttl_drift:
                ttl_drift = spread
        if epoch > split_epoch and len({it["member"] for it in valid}) < q:
            line_synced = False
        for it in valid:
            live.add(it["member"])
        accepted[seq] = epoch
    cycle_chain = 0
    s = 1
    while True:
        if s <= wm or s in accepted:
            cycle_chain = s
            s += 1
        else:
            break
    stable_phase = 0
    for seq, seq_rows in all_rows.items():
        if seq > cycle_chain:
            continue
        for entry in seq_rows:
            if seq in accepted and entry["epoch"] == accepted[seq]:
                if _crc16(entry["seq"], entry["payload"]) == entry["crc"] and entry["epoch"] > stable_phase:
                    stable_phase = entry["epoch"]
            elif seq <= wm and entry["epoch"] > stable_phase:
                stable_phase = entry["epoch"]
    spread = max(offsets.values()) - min(offsets.values())
    lag = "tight" if spread <= lag_tight else "wide"
    digest = _digest_hex(
        line_id, stable_phase, cycle_chain, purge, stale, len(live), lag, line_synced, ttl_drift
    )
    return {
        "schema_version": "1",
        "line_id": line_id,
        "stable_phase": stable_phase,
        "cycle_chain": cycle_chain,
        "defect_purges": purge,
        "orphan_cycles": stale,
        "stations_live": len(live),
        "jitter_band": lag,
        "line_synced": line_synced,
        "skew_drift_max": ttl_drift,
        "digest_hex": digest,
    }


def _swap(line_name: str) -> None:
    src = FIXTURES / line_name
    assert src.is_dir()
    if ACTIVE.exists():
        shutil.rmtree(ACTIVE)
    shutil.copytree(src, ACTIVE)


def _run_tool() -> dict:
    if OUT.exists():
        OUT.unlink()
    env = {**os.environ, "TB_LINE_FIXTURE": "1", "GOFLAGS": "-mod=mod", "CGO_ENABLED": "1"}
    subprocess.run([VERIFY_BIN], cwd="/app", env=env, check=True)
    raw = json.loads(OUT.read_text())
    assert raw["schema_version"] == "1"
    return raw


def test_alpha_sync_report() -> None:
    """Alpha line pack should reach tight jitter band with full five-station chain."""
    _swap("line_alpha")
    exp = _expected_from_fixture("line_alpha")
    got = _run_tool()
    assert got == exp


def test_beta_wide_jitter_band() -> None:
    """Beta clock offsets exceed the configured tight jitter band."""
    _swap("line_beta")
    exp = _expected_from_fixture("line_beta")
    got = _run_tool()
    assert got["jitter_band"] == exp["jitter_band"]
    assert got["cycle_chain"] == exp["cycle_chain"]


def test_gamma_stale_after_lone_gen() -> None:
    """Gamma stops the chain when only one station carries a high generation row."""
    _swap("line_gamma")
    exp = _expected_from_fixture("line_gamma")
    got = _run_tool()
    assert got["orphan_cycles"] == exp["orphan_cycles"]
    assert got["cycle_chain"] == exp["cycle_chain"]


def test_delta_high_stale_count() -> None:
    """Delta orphan high tick should not extend the cycle chain."""
    _swap("line_delta")
    exp = _expected_from_fixture("line_delta")
    got = _run_tool()
    assert got["orphan_cycles"] == exp["orphan_cycles"]
    assert got["cycle_chain"] == exp["cycle_chain"]


def test_epsilon_defect_purges_nonzero() -> None:
    """Epsilon should count one defect purge on the winning phase group."""
    _swap("line_epsilon")
    exp = _expected_from_fixture("line_epsilon")
    got = _run_tool()
    assert got["defect_purges"] == exp["defect_purges"]
    assert got["cycle_chain"] == exp["cycle_chain"]


def test_alpha_cycle_chain_watermark() -> None:
    """Alpha commit watermark must use the minimum mark, not the maximum."""
    _swap("line_alpha")
    exp = _expected_from_fixture("line_alpha")
    got = _run_tool()
    assert got["cycle_chain"] == exp["cycle_chain"]


def test_go_subsystem_tests_pass() -> None:
    """Go unit tests under /app must pass after the repair."""
    subprocess.run(
        [GO_BIN, "test", "./..."],
        cwd="/app",
        env={**os.environ, "GOFLAGS": "-mod=mod", "CGO_ENABLED": "1"},
        check=True,
    )
