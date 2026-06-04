"""Verifier for /app/output/verdict_bundle.json and marked layout sketches."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess

import pytest
from copy import deepcopy
from pathlib import Path

APP = Path("/app")
BUNDLE = APP / "output" / "verdict_bundle.json"
MARKED_DIR = APP / "output" / "marked"
REGISTRY = APP / "config" / "case_registry.json"
RUN_PACK = APP / "flow-src" / "run_pack.lua"

PACK_IDS = [
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "iota",
    "zeta",
]

ROW_FIELDS = (
    "row_id",
    "route_state",
    "window_state",
    "identity_hex",
    "chain_ok",
    "walk_ok",
    "handoff_ok",
    "path_ids",
    "ledger_hits",
)

ROUTE_STATES = frozenset({"cleared", "blocked", "held"})
WINDOW_STATES = frozenset({"live", "preopen", "expired"})
STYLE_TOKENS = ("deny_fill", "live_fill", "cleared_fill")

def _openssl_sha256_fingerprint(pem_path: Path) -> str:
    proc = subprocess.run(
        [
            "openssl",
            "x509",
            "-in",
            str(pem_path),
            "-noout",
            "-fingerprint",
            "-sha256",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    line = proc.stdout.strip()
    hex_part = line.split("=", 1)[-1]
    return hex_part.replace(":", "").lower()


def _run_sweep() -> int:
    """Re-run pack drivers and merge fragments (verifier-owned, not the sweep script)."""
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    sweep_rc = 0
    packs: list[dict] = []
    failed: list[str] = []
    for pack_id in reg["pack_ids"]:
        runner = APP / "flow-src" / f"run_{pack_id}.lua"
        cmd = ["lua5.4", str(runner)] if runner.is_file() else ["lua5.4", str(RUN_PACK), pack_id]
        proc = subprocess.run(cmd, cwd=str(APP), check=False)
        sweep_rc |= int(proc.returncode)
        data = json.loads((APP / "output" / f".pack_{pack_id}.json").read_text(encoding="utf-8"))
        packs.append(data)
        if data.get("pack_rc", 0) != 0:
            failed.append(pack_id)
    failed.sort()
    run_id = hashlib.sha256(
        json.dumps(packs, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]
    doc = {
        "run_id": run_id,
        "packs": packs,
        "aggregate": {
            "failed_packs": len(failed),
            "failed_pack_ids": failed,
        },
    }
    BUNDLE.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return sweep_rc


def _load_bundle() -> dict:
    assert BUNDLE.is_file(), f"missing bundle at {BUNDLE}"
    data = json.loads(BUNDLE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _pack_map(bundle: dict) -> dict[str, dict]:
    packs = bundle.get("packs", [])
    assert isinstance(packs, list)
    return {p["pack_id"]: p for p in packs}


def _row_by_id(pack: dict, row_id: str) -> dict:
    for row in pack.get("rows", []):
        if row.get("row_id") == row_id:
            return row
    raise AssertionError(f"row {row_id!r} not found in pack {pack.get('pack_id')!r}")


def _node_ids_from_dot(dot_path: Path) -> set[str]:
    ids: set[str] = set()
    for line in dot_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r'\s*([A-Za-z_][\w_]*)\s*\[', line)
        if m:
            ids.add(m.group(1))
    return ids


def _identity_bundle_digest(bundle: dict) -> str:
    values: list[str] = []
    for pack in bundle["packs"]:
        for row in pack["rows"]:
            hx = row.get("identity_hex", "")
            if hx:
                values.append(hx)
    joined = ",".join(sorted(values))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _bundle_without_run_id(bundle: dict) -> dict:
    trimmed = deepcopy(bundle)
    trimmed.pop("run_id", None)
    return trimmed


def _fillcolor_for_node(dot_text: str, node_id: str) -> str | None:
    for line in dot_text.splitlines():
        stripped = line.strip()
        if stripped.startswith(node_id + " ") or stripped.startswith(node_id + "["):
            match = re.search(r'fillcolor="([^"]+)"', stripped)
            if match:
                return match.group(1)
    return None


def _rows_iter(bundle: dict):
    for pack in bundle["packs"]:
        for row in pack["rows"]:
            yield pack["pack_id"], row


def _pack_ids_with_rc(bundle: dict) -> set[str]:
    return {p["pack_id"] for p in bundle["packs"] if p.get("pack_rc", 0) != 0}


@pytest.fixture(scope="module")
def sweep_rc() -> int:
    return _run_sweep()


@pytest.fixture(scope="module")
def bundle(sweep_rc: int) -> dict:
    return _load_bundle()


@pytest.fixture(scope="module", autouse=True)
def _require_repaired_walker(bundle: dict) -> None:
    """Most contract tests assume deny-ledger rows are blocked, not cleared."""
    row = _row_by_id(_pack_map(bundle)["alpha"], "svc_a")
    if row["route_state"] != "blocked":
        pytest.fail(
            "chainwalk still paints deny-ledger rows as cleared; repair graph/policy gate"
        )


def test_report_top_keys(bundle: dict) -> None:
    """Bundle exposes run_id, packs, and aggregate sections."""
    assert set(bundle.keys()) >= {"run_id", "packs", "aggregate"}
    assert isinstance(bundle["run_id"], str) and len(bundle["run_id"]) == 16
    agg = bundle["aggregate"]
    assert "failed_packs" in agg and "failed_pack_ids" in agg


def test_alpha_block_stays_blocked(bundle: dict) -> None:
    """Deny-ledger service row must not be promoted to cleared."""
    row = _row_by_id(_pack_map(bundle)["alpha"], "svc_a")
    assert row["ledger_hits"] >= 1
    assert row["route_state"] == "blocked"
    assert row["handoff_ok"] is False


def test_alpha_second_row_can_clear(bundle: dict) -> None:
    """Non-ledger service row on alpha may clear when chain and walk succeed."""
    row = _row_by_id(_pack_map(bundle)["alpha"], "svc_b")
    assert row["route_state"] == "cleared"
    assert row["handoff_ok"] is True
    assert row["chain_ok"] is True
    assert row["walk_ok"] is True


def test_beta_preopen_row_flag(bundle: dict) -> None:
    """Future-validity leaf must surface preopen window_state."""
    row = _row_by_id(_pack_map(bundle)["beta"], "beta_leaf")
    assert row["window_state"] == "preopen"
    assert row["handoff_ok"] is False


def test_beta_window_not_expired(bundle: dict) -> None:
    """Pre-open beta leaf must not be classified as expired."""
    row = _row_by_id(_pack_map(bundle)["beta"], "beta_leaf")
    assert row["window_state"] != "expired"


def test_gamma_broken_path_rc(sweep_rc: int, bundle: dict) -> None:
    """Severed/broken gamma pack contributes to non-zero sweep RC."""
    assert _pack_map(bundle)["gamma"]["pack_rc"] == 1
    assert sweep_rc != 0


def test_gamma_closure_and_chain_both_false(bundle: dict) -> None:
    """Gamma row must fail both closure and chain gates."""
    row = _row_by_id(_pack_map(bundle)["gamma"], "gamma_leaf")
    assert row["walk_ok"] is False
    assert row["chain_ok"] is False


def test_delta_good_path_ok(bundle: dict) -> None:
    """Delta valid chain clears with live window."""
    row = _row_by_id(_pack_map(bundle)["delta"], "delta_leaf")
    assert row["route_state"] == "cleared"
    assert row["window_state"] == "live"
    assert row["handoff_ok"] is True


def test_delta_path_chain_order(bundle: dict) -> None:
    """Delta path_ids follow leaf-first ordering toward anchor."""
    row = _row_by_id(_pack_map(bundle)["delta"], "delta_leaf")
    assert row["path_ids"] == ["delta_leaf", "intermediate", "anchor"]


def test_delta_fingerprint_matches_live_cred(bundle: dict) -> None:
    """Delta identity_hex must match live OpenSSL SHA-256 fingerprint."""
    row = _row_by_id(_pack_map(bundle)["delta"], "delta_leaf")
    leaf = APP / "cases" / "delta" / "certs" / "leaf.pem"
    expected = _openssl_sha256_fingerprint(leaf)
    assert row["identity_hex"] == expected
    assert len(row["identity_hex"]) == 64


def test_dot_annotation_styles(bundle: dict) -> None:
    """Marked alpha sketch applies deny, live, and cleared fill tokens."""
    marked = MARKED_DIR / "alpha.dot"
    assert marked.is_file()
    text = marked.read_text(encoding="utf-8")
    assert "deny_fill" in text
    assert "cleared_fill" in text
    # svc_b cleared + live window uses live_fill or cleared_fill
    assert "live_fill" in text or "cleared_fill" in text


def test_marked_preserves_node_ids(bundle: dict) -> None:
    """Marked copies retain every node id from the source sketch."""
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for pack_id in reg["pack_ids"]:
        src = APP / "cases" / pack_id / "layout.dot"
        marked = MARKED_DIR / f"{pack_id}.dot"
        assert marked.is_file(), f"missing marked sketch for {pack_id}"
        src_ids = _node_ids_from_dot(src)
        marked_ids = _node_ids_from_dot(marked)
        assert src_ids <= marked_ids, f"{pack_id}: node ids dropped in marked copy"


def test_registry_row_totals(bundle: dict) -> None:
    """aggregate.failed_packs matches failed_pack_ids length."""
    agg = bundle["aggregate"]
    failed_ids = agg["failed_pack_ids"]
    assert agg["failed_packs"] == len(failed_ids)
    assert all(isinstance(pid, str) for pid in failed_ids)


def test_failed_pack_ids_sorted(bundle: dict) -> None:
    """failed_pack_ids stay lexicographically sorted."""
    ids = bundle["aggregate"]["failed_pack_ids"]
    assert ids == sorted(ids)


def test_fingerprint_hex_width(bundle: dict) -> None:
    """Every non-empty identity_hex is 64 lowercase hex chars (SHA-256 class)."""
    for pack in bundle["packs"]:
        for row in pack["rows"]:
            hx = row["identity_hex"]
            if not hx:
                continue
            assert len(hx) == 64
            assert re.fullmatch(r"[0-9a-f]{64}", hx)


def test_zeta_expired_window_state(bundle: dict) -> None:
    """Expired zeta leaf reports expired window_state."""
    row = _row_by_id(_pack_map(bundle)["zeta"], "zeta_leaf")
    assert row["window_state"] == "expired"
    assert row["handoff_ok"] is False


def test_epsilon_anchor_alone_ok(bundle: dict) -> None:
    """Anchor-only epsilon pack succeeds with zero pack_rc."""
    pack = _pack_map(bundle)["epsilon"]
    assert pack["pack_rc"] == 0
    row = _row_by_id(pack, "anchor")
    assert row["handoff_ok"] is True
    assert row["route_state"] == "cleared"


def test_epsilon_single_row_no_intermediate(bundle: dict) -> None:
    """Epsilon emits one row with empty path_ids."""
    pack = _pack_map(bundle)["epsilon"]
    assert len(pack["rows"]) == 1
    row = pack["rows"][0]
    assert row["row_id"] == "anchor"
    assert row["path_ids"] == []


def test_driver_rc_on_failure(sweep_rc: int, bundle: dict) -> None:
    """Sweep RC is non-zero whenever aggregate lists failed packs."""
    agg = bundle["aggregate"]
    if agg["failed_packs"] > 0:
        assert sweep_rc != 0
    else:
        assert sweep_rc == 0


def test_sweep_idempotent_bundle(bundle: dict) -> None:
    """Two consecutive sweeps yield identical pack payloads (excluding run_id)."""
    first = _bundle_without_run_id(bundle)
    _run_sweep()
    second = _bundle_without_run_id(_load_bundle())
    assert first == second


def test_marked_file_count_matches_registry(bundle: dict) -> None:
    """Exactly one marked sketch exists per registry pack id."""
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for pack_id in reg["pack_ids"]:
        assert (MARKED_DIR / f"{pack_id}.dot").is_file()
    extra = [p.name for p in MARKED_DIR.glob("*.dot")]
    assert len(extra) == len(reg["pack_ids"])


def test_case_rc_matches_row_handoff_ok(bundle: dict) -> None:
    """pack_rc is zero iff every row handoff_ok is true."""
    for pack in bundle["packs"]:
        rows = pack["rows"]
        all_ok = all(r["handoff_ok"] for r in rows)
        if all_ok:
            assert pack["pack_rc"] == 0
        else:
            assert pack["pack_rc"] == 1


def test_identity_bundle_digest_stable(bundle: dict) -> None:
    """Sorted identity hex join produces a stable bundle digest."""
    digest = _identity_bundle_digest(bundle)
    assert len(digest) == 64
    # Recompute from fixture certs after sweep; must be deterministic across runs.
    _run_sweep()
    again = _identity_bundle_digest(_load_bundle())
    assert digest == again


def test_row_schema_domains(bundle: dict) -> None:
    """Row enums and types match bundle_schema.md."""
    for pack in bundle["packs"]:
        assert pack["pack_id"] in PACK_IDS
        for row in pack["rows"]:
            for field in ROW_FIELDS:
                assert field in row
            assert row["route_state"] in ROUTE_STATES
            assert row["window_state"] in WINDOW_STATES
            assert isinstance(row["chain_ok"], bool)
            assert isinstance(row["walk_ok"], bool)
            assert isinstance(row["handoff_ok"], bool)
            assert isinstance(row["path_ids"], list)
            assert isinstance(row["ledger_hits"], int)


def test_alpha_listed_when_deny_row_blocked(bundle: dict) -> None:
    """Alpha appears among failed_pack_ids when deny row is blocked."""
    alpha = _pack_map(bundle)["alpha"]
    svc_a = _row_by_id(alpha, "svc_a")
    assert svc_a["route_state"] == "blocked"
    assert "alpha" in bundle["aggregate"]["failed_pack_ids"]


def test_delta_intermediate_fingerprint_matches_store(bundle: dict) -> None:
    """Intermediate PEM fingerprint is stable and distinct from leaf."""
    leaf_row = _row_by_id(_pack_map(bundle)["delta"], "delta_leaf")
    leaf_fp = _openssl_sha256_fingerprint(APP / "cases" / "delta" / "certs" / "leaf.pem")
    inter_fp = _openssl_sha256_fingerprint(
        APP / "cases" / "delta" / "certs" / "intermediate.pem"
    )
    assert leaf_row["identity_hex"] == leaf_fp
    assert leaf_fp != inter_fp


def test_gamma_marked_sketch_mentions_severed(bundle: dict) -> None:
    """Gamma marked sketch preserves severed annotation from source layout."""
    src = (APP / "cases" / "gamma" / "layout.dot").read_text(encoding="utf-8")
    marked = (MARKED_DIR / "gamma.dot").read_text(encoding="utf-8")
    assert "severed" in src
    assert "gamma_leaf" in marked


def test_registry_case_order_matches_bundle(bundle: dict) -> None:
    """packs array follows case_registry.json order."""
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert [p["pack_id"] for p in bundle["packs"]] == reg["pack_ids"]


def test_path_ids_lead_with_row_id(bundle: dict) -> None:
    """Every non-empty path_ids list begins with the row's own node id."""
    for _pack_id, row in _rows_iter(bundle):
        path = row["path_ids"]
        if not path:
            continue
        assert path[0] == row["row_id"], (
            f"{_pack_id}/{row['row_id']}: path_ids must start at the service node"
        )


def test_path_ids_terminate_at_anchor(bundle: dict) -> None:
    """Successful walks end at the anchor node id."""
    for _pack_id, row in _rows_iter(bundle):
        if not row["walk_ok"]:
            continue
        path = row["path_ids"]
        if not path:
            continue
        assert path[-1] == "anchor", (
            f"{_pack_id}/{row['row_id']}: path_ids must terminate at anchor"
        )


def test_aggregate_rc_ids_match_case_bits(bundle: dict) -> None:
    """failed_pack_ids equals the set of pack ids whose pack_rc is non-zero."""
    agg_ids = set(bundle["aggregate"]["failed_pack_ids"])
    rc_ids = _pack_ids_with_rc(bundle)
    assert agg_ids == rc_ids
    assert bundle["aggregate"]["failed_packs"] == len(agg_ids)


def test_marked_alpha_node_a_style_token(bundle: dict) -> None:
    """Blocked svc_a node in the alpha marked sketch uses deny_fill."""
    marked = MARKED_DIR / "alpha.dot"
    token = _fillcolor_for_node(marked.read_text(encoding="utf-8"), "svc_a")
    assert token == "deny_fill"


def test_marked_delta_leaf_ok_fill(bundle: dict) -> None:
    """Cleared delta_leaf node in the delta marked sketch uses cleared_fill."""
    marked = MARKED_DIR / "delta.dot"
    token = _fillcolor_for_node(marked.read_text(encoding="utf-8"), "delta_leaf")
    assert token == "cleared_fill"


def test_chain_ok_implies_identity_hex(bundle: dict) -> None:
    """Rows with chain_ok true must carry a 64-char lowercase identity_hex."""
    for pack_id, row in _rows_iter(bundle):
        if not row["chain_ok"]:
            continue
        hx = row["identity_hex"]
        assert hx and len(hx) == 64, f"{pack_id}/{row['row_id']}: missing sha256-class identity"
        assert hx == hx.lower() and re.fullmatch(r"[0-9a-f]{64}", hx)


def test_closure_path_coherence(bundle: dict) -> None:
    """walk_ok true with a multi-hop path must include anchor and start at row_id."""
    for pack_id, row in _rows_iter(bundle):
        if not row["walk_ok"]:
            continue
        path = row["path_ids"]
        if len(path) < 2:
            continue
        assert path[0] == row["row_id"]
        assert "anchor" in path


def test_ok_route_requires_closure_chain(bundle: dict) -> None:
    """route_state cleared requires both walk_ok and chain_ok."""
    for pack_id, row in _rows_iter(bundle):
        if row["route_state"] != "cleared":
            continue
        assert row["walk_ok"] and row["chain_ok"], (
            f"{pack_id}/{row['row_id']}: cleared route without walk/chain success"
        )


def test_preopen_rows_never_ok_route(bundle: dict) -> None:
    """preopen window_state forbids cleared route_state and handoff_ok true."""
    for pack_id, row in _rows_iter(bundle):
        if row["window_state"] != "preopen":
            continue
        assert row["route_state"] != "cleared"
        assert row["handoff_ok"] is False


def test_expired_rows_never_ok_route(bundle: dict) -> None:
    """expired window_state forbids cleared route_state and handoff_ok true."""
    for pack_id, row in _rows_iter(bundle):
        if row["window_state"] != "expired":
            continue
        assert row["route_state"] != "cleared"
        assert row["handoff_ok"] is False


def test_iota_serves_expansion_reaches_anchor(bundle: dict) -> None:
    """Iota row connects via serves first hop; walk must still reach anchor."""
    row = _row_by_id(_pack_map(bundle)["iota"], "iota_row")
    assert row["walk_ok"] is True
    assert row["path_ids"][-1] == "anchor"
    assert "iota_cred" in row["path_ids"]


def test_iota_row_clears_when_chain_valid(bundle: dict) -> None:
    """Iota valid three-level chain clears after serves expansion."""
    row = _row_by_id(_pack_map(bundle)["iota"], "iota_row")
    assert row["route_state"] == "cleared"
    assert row["handoff_ok"] is True
    assert row["chain_ok"] is True


def test_alpha_ledger_hits_positive_on_deny_target(bundle: dict) -> None:
    """Deny edges into svc_a increment ledger_hits (see edge_legend direction)."""
    row = _row_by_id(_pack_map(bundle)["alpha"], "svc_a")
    assert row["ledger_hits"] >= 1


def test_delta_chain_ok_with_store_wiring(bundle: dict) -> None:
    """Delta intermediate store wiring must yield chain_ok true."""
    row = _row_by_id(_pack_map(bundle)["delta"], "delta_leaf")
    assert row["chain_ok"] is True


def test_iota_case_present_in_bundle(bundle: dict) -> None:
    """Bundle includes iota case between epsilon and zeta."""
    ids = [p["pack_id"] for p in bundle["packs"]]
    assert ids.index("iota") == ids.index("epsilon") + 1


def test_no_cleared_row_with_positive_ledger_hits(bundle: dict) -> None:
    """ledger_hits > 0 must never pair with route_state cleared."""
    for pack_id, row in _rows_iter(bundle):
        if row["ledger_hits"] > 0:
            assert row["route_state"] != "cleared", f"{pack_id}/{row['row_id']}"


def test_iota_absent_from_failed_when_cleared(bundle: dict) -> None:
    """Iota must not appear in failed_pack_ids when its row clears."""
    iota = _pack_map(bundle)["iota"]
    row = _row_by_id(iota, "iota_row")
    if row["route_state"] == "cleared" and row["handoff_ok"]:
        assert "iota" not in bundle["aggregate"]["failed_pack_ids"]


def test_runtime_tz_base_documented(bundle: dict) -> None:
    """Fixture registry declares UTC wall-clock basis for audits."""
    env = (APP / "config" / "runtime.env").read_text(encoding="utf-8")
    assert "TZ_BASE=UTC" in env


def test_iota_cred_node_on_closure_path(bundle: dict) -> None:
    """Serves expansion must traverse the credential node id."""
    row = _row_by_id(_pack_map(bundle)["iota"], "iota_row")
    assert row["walk_ok"]
    assert row["path_ids"][0] == "iota_row"
    assert "iota_cred" in row["path_ids"][1:]


def test_run_cases_script_exits_nonzero_on_failure(bundle: dict) -> None:
    """bash run_cases.sh must exit non-zero when any pack records a failed handoff."""
    proc = subprocess.run(
        ["bash", "/app/platform/run_cases.sh"],
        cwd="/app",
        check=False,
    )
    refreshed = json.loads(BUNDLE.read_text(encoding="utf-8"))
    if refreshed["aggregate"]["failed_packs"] > 0:
        assert proc.returncode != 0, (
            "run_cases.sh returned 0 despite failing packs; "
            "sweep exit accumulation is not propagating all pack failures"
        )
    else:
        assert proc.returncode == 0


def test_bundle_merge_run_id_stable(bundle: dict) -> None:
    """bundle_merge.py run_id is identical across back-to-back invocations and 16 chars wide."""
    subprocess.run(
        ["python3", "/app/scripts/bundle_merge.py"],
        cwd="/app",
        check=True,
    )
    first_id = json.loads(BUNDLE.read_text(encoding="utf-8"))["run_id"]

    subprocess.run(
        ["python3", "/app/scripts/bundle_merge.py"],
        cwd="/app",
        check=True,
    )
    second_id = json.loads(BUNDLE.read_text(encoding="utf-8"))["run_id"]

    assert len(first_id) == 16, f"run_id width {len(first_id)} != 16"
    assert first_id == second_id, (
        "run_id changed across consecutive bundle_merge.py calls; "
        "run_id must be stable when the input pack fragments do not change"
    )

