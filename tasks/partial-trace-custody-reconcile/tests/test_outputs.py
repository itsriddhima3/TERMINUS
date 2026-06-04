"""Verifier for custody bundle with graph-ledger reference reconciliation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

APP = Path("/app")
BUNDLE = APP / "output" / "custody_bundle.json"
RANKS_PATH = APP / "config" / "channel_ranks.json"
SCENARIOS = APP / "config" / "scenarios.json"

PACK_IDS = ["alpha", "beta", "gamma", "delta"]

LEDGER_FIELDS = ("tick", "object", "from", "to", "inferred")
PROOF_FIELDS = (
    "single_holder_ok",
    "acyclic_ok",
    "gap_fill_count",
    "contradiction_resolved",
    "ledger_digest",
)


def _build() -> None:
    subprocess.run(["bash", "/app/scripts/build.sh"], check=True, cwd="/app")


def _run_sweep() -> None:
    _build()
    subprocess.run(["bash", "/app/platform/run_scenarios.sh"], check=True, cwd="/app")


def _load_bundle() -> dict[str, Any]:
    assert BUNDLE.is_file(), f"missing bundle at {BUNDLE}"
    data = json.loads(BUNDLE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _load_ranks() -> dict[str, int]:
    doc = json.loads(RANKS_PATH.read_text(encoding="utf-8"))
    return {str(k): int(v) for k, v in doc["ranks"].items()}


def _parse_channel(path: Path, channel: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if parts[0] == "see":
            events.append(
                {
                    "kind": "see",
                    "tick": int(parts[1]),
                    "object": parts[2],
                    "holder": parts[3],
                    "channel": channel,
                }
            )
        elif parts[0] == "xfer":
            events.append(
                {
                    "kind": "xfer",
                    "tick": int(parts[1]),
                    "object": parts[2],
                    "from": parts[3],
                    "to": parts[4],
                    "channel": channel,
                }
            )
    return events


def _reference_pack(pack_dir: Path, ranks: dict[str, int]) -> dict[str, Any]:
    meta = json.loads((pack_dir / "meta.json").read_text(encoding="utf-8"))
    events: list[dict[str, Any]] = []
    ch_dir = pack_dir / "channels"
    for ch_file in sorted(ch_dir.glob("*.txt")):
        events.extend(_parse_channel(ch_file, ch_file.stem))

    xfer_keys = {
        (ev["tick"], ev["object"])
        for ev in events
        if ev["kind"] == "xfer"
    }

    resolved: list[dict[str, Any]] = [
        ev for ev in events if ev["kind"] == "xfer"
    ]
    contradictions = 0

    by_key: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for ev in events:
        if ev["kind"] == "see":
            by_key[(ev["tick"], ev["object"])].append(ev)

    for (tick, obj), group in sorted(by_key.items()):
        if (tick, obj) in xfer_keys:
            continue
        holders = {ev["holder"] for ev in group}
        if len(holders) > 1:
            contradictions += 1
            best = group[0]
            for ev in group[1:]:
                r_best = ranks.get(best["channel"], 0)
                r_cur = ranks.get(ev["channel"], 0)
                if r_cur > r_best or (r_cur == r_best and ev["channel"] > best["channel"]):
                    best = ev
            resolved.append(
                {
                    "kind": "see",
                    "tick": tick,
                    "object": obj,
                    "holder": best["holder"],
                }
            )
        else:
            resolved.append(
                {
                    "kind": "see",
                    "tick": tick,
                    "object": obj,
                    "holder": group[0]["holder"],
                }
            )

    initial = meta.get("initial_holders", {})
    ledger: list[dict[str, Any]] = []
    xfer_at: dict[str, dict[int, tuple[str, str]]] = defaultdict(dict)
    for ev in resolved:
        if ev["kind"] == "xfer":
            xfer_at[ev["object"]][ev["tick"]] = (ev["from"], ev["to"])
            ledger.append(
                {
                    "tick": ev["tick"],
                    "object": ev["object"],
                    "from": ev["from"],
                    "to": ev["to"],
                    "inferred": False,
                }
            )

    objects: dict[str, str] = dict(initial)
    for ev in resolved:
        objects.setdefault(ev["object"], "")

    for obj, start in sorted(objects.items()):
        points: list[tuple[int, str, bool]] = []
        for ev in resolved:
            if ev.get("object") != obj:
                continue
            if ev["kind"] == "xfer":
                points.append((ev["tick"], ev["to"], True))
            elif ev["kind"] == "see":
                points.append((ev["tick"], ev["holder"], False))
        points.sort(key=lambda x: (x[0], x[2]))

        cur = start
        for tick, holder, is_xfer in points:
            if is_xfer:
                cur = holder
                continue
            if holder != cur:
                if tick not in xfer_at.get(obj, {}):
                    ledger.append(
                        {
                            "tick": tick,
                            "object": obj,
                            "from": cur,
                            "to": holder,
                            "inferred": True,
                        }
                    )
                cur = holder

    ledger.sort(key=lambda r: (r["object"], r["tick"], r["from"], r["to"]))

    gap_fill = sum(1 for r in ledger if r["inferred"])
    acyclic_ok = _check_acyclic(ledger)
    digest = _digest_ledger(ledger)
    proof = {
        "single_holder_ok": acyclic_ok and bool(ledger),
        "acyclic_ok": acyclic_ok,
        "gap_fill_count": gap_fill,
        "contradiction_resolved": contradictions,
        "ledger_digest": digest,
    }
    return {
        "pack_id": meta["pack_id"],
        "transition_ledger": ledger,
        "consistency_proof": proof,
        "pack_ok": proof["single_holder_ok"] and proof["acyclic_ok"],
    }


def _check_acyclic(ledger: list[dict[str, Any]]) -> bool:
    by_obj: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger:
        by_obj[row["object"]].append(row)
    for rows in by_obj.values():
        rows.sort(key=lambda r: (r["tick"], r["from"], r["to"]))
        for i in range(1, len(rows)):
            if rows[i - 1]["to"] != rows[i]["from"] or rows[i]["tick"] < rows[i - 1]["tick"]:
                return False
    return True


def _digest_ledger(ledger: list[dict[str, Any]]) -> str:
    body = json.dumps(ledger, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _pack_map(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    packs = bundle.get("packs", [])
    assert isinstance(packs, list)
    return {p["pack_id"]: p for p in packs}


def _write_pack_dir(
    root: Path,
    pack_id: str,
    initial_holders: dict[str, str],
    channels: dict[str, str],
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "meta.json").write_text(
        json.dumps({"pack_id": pack_id, "initial_holders": initial_holders}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    ch = root / "channels"
    ch.mkdir(exist_ok=True)
    for channel_id, body in channels.items():
        (ch / f"{channel_id}.txt").write_text(body.strip() + "\n", encoding="utf-8")
    return root


def _run_isolated_pack(pack_dir: Path) -> dict[str, Any]:
    _build()
    meta = json.loads((pack_dir / "meta.json").read_text(encoding="utf-8"))
    pack_id = str(meta["pack_id"])
    out = Path("/app/output") / f".pack_{pack_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["/app/bin/route_pack", str(pack_dir), str(out)],
        check=True,
        cwd="/app",
    )
    return json.loads(out.read_text(encoding="utf-8"))


def _assert_pack_matches_reference(
    pack_dir: Path, ranks: dict[str, int] | None = None
) -> dict[str, Any]:
    ranks = ranks or _load_ranks()
    ref = _reference_pack(pack_dir, ranks)
    got = _run_isolated_pack(pack_dir)
    assert got["transition_ledger"] == ref["transition_ledger"]
    assert got["consistency_proof"] == ref["consistency_proof"]
    assert got["pack_ok"] == ref["pack_ok"]
    assert got["pack_ok"] is True
    return got


def test_bundle_schema() -> None:
    """Top-level bundle keys and pack row shapes match the documented contract."""
    _run_sweep()
    bundle = _load_bundle()
    assert set(bundle.keys()) == {"run_id", "packs", "aggregate"}
    assert isinstance(bundle["run_id"], str) and len(bundle["run_id"]) == 16
    agg = bundle["aggregate"]
    assert set(agg.keys()) == {"failed_packs", "failed_pack_ids"}
    ids = [p["pack_id"] for p in bundle["packs"]]
    assert ids == sorted(ids)
    for pack in bundle["packs"]:
        assert set(pack.keys()) == {
            "pack_id",
            "transition_ledger",
            "consistency_proof",
            "pack_ok",
        }
        assert isinstance(pack["transition_ledger"], list)
        proof = pack["consistency_proof"]
        assert set(proof.keys()) == set(PROOF_FIELDS)
        for row in pack["transition_ledger"]:
            assert set(row.keys()) == set(LEDGER_FIELDS)


def test_all_bundled_packs_ok() -> None:
    """Every shipped scenario pack must reach pack_ok with zero aggregate failures."""
    _run_sweep()
    bundle = _load_bundle()
    assert bundle["aggregate"]["failed_packs"] == 0
    assert bundle["aggregate"]["failed_pack_ids"] == []
    for pack in bundle["packs"]:
        assert pack["pack_ok"] is True


def test_transition_ledger_matches_reference() -> None:
    """Inferred graph rows must match verifier-owned reconciliation for bundled packs."""
    _run_sweep()
    bundle = _load_bundle()
    ranks = _load_ranks()
    by_id = _pack_map(bundle)
    for pack_id in PACK_IDS:
        ref = _reference_pack(APP / "cases" / pack_id, ranks)
        got = by_id[pack_id]["transition_ledger"]
        assert got == ref["transition_ledger"], pack_id


def test_consistency_proof_matches_reference() -> None:
    """Proof counters and ledger digest must reflect the inferred transition ledger."""
    _run_sweep()
    bundle = _load_bundle()
    ranks = _load_ranks()
    by_id = _pack_map(bundle)
    for pack_id in PACK_IDS:
        ref = _reference_pack(APP / "cases" / pack_id, ranks)
        assert by_id[pack_id]["consistency_proof"] == ref["consistency_proof"], pack_id


def test_alpha_gap_fill_inferred_steps() -> None:
    """Alpha partial channels require inferred movement rows bridging sightings."""
    _run_sweep()
    pack = _pack_map(_load_bundle())["alpha"]
    inferred = [r for r in pack["transition_ledger"] if r["inferred"]]
    assert len(inferred) >= 2
    assert pack["consistency_proof"]["gap_fill_count"] == len(inferred)


def test_beta_contradiction_resolution() -> None:
    """Beta same-tick channel conflict must resolve via rank, not holder lex order."""
    _run_sweep()
    pack = _pack_map(_load_bundle())["beta"]
    assert pack["consistency_proof"]["contradiction_resolved"] >= 1
    at_five = [r for r in pack["transition_ledger"] if r["tick"] == 5 and r["object"] == "unit-b"]
    assert any(r["to"] == "vault-1" for r in at_five)


def test_gamma_explicit_handoff_row() -> None:
    """Gamma mixes explicit handoff lines with partial sightings requiring inference."""
    _run_sweep()
    pack = _pack_map(_load_bundle())["gamma"]
    explicit = [r for r in pack["transition_ledger"] if not r["inferred"]]
    inferred = [r for r in pack["transition_ledger"] if r["inferred"]]
    assert len(explicit) >= 1
    assert len(inferred) >= 1
    assert pack["consistency_proof"]["gap_fill_count"] == len(inferred)


def test_run_id_stable_on_repeat() -> None:
    """Repeated sweeps over the same packs yield identical run_id and ledger digests."""
    _run_sweep()
    first = deepcopy(_load_bundle())
    _run_sweep()
    second = _load_bundle()
    assert first["run_id"] == second["run_id"]
    for pid in PACK_IDS:
        d1 = _pack_map(first)[pid]["consistency_proof"]["ledger_digest"]
        d2 = _pack_map(second)[pid]["consistency_proof"]["ledger_digest"]
        assert d1 == d2


def test_registry_covers_bundled_ids() -> None:
    """Scenario registry lists exactly the bundled example pack ids."""
    reg = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    assert reg["scenario_ids"] == PACK_IDS


def test_epsilon_three_channel_conflict_north_prevails() -> None:
    """Three channels disagree at one tick; highest rank channel must win the sighting."""
    ranks = _load_ranks()
    ref = _reference_pack(APP / "cases" / "epsilon", ranks)
    got = _assert_pack_matches_reference(APP / "cases" / "epsilon", ranks)
    assert ref["consistency_proof"]["contradiction_resolved"] == 1
    rows = [r for r in got["transition_ledger"] if r["tick"] == 10]
    assert len(rows) == 1
    assert rows[0]["inferred"] is True
    assert rows[0]["from"] != rows[0]["to"]


def test_zeta_handoff_suppresses_same_tick_contradiction() -> None:
    """Explicit handoff at a tick must not increment contradiction_resolved against sees."""
    got = _assert_pack_matches_reference(APP / "cases" / "zeta")
    assert got["consistency_proof"]["contradiction_resolved"] == 0
    explicit = [r for r in got["transition_ledger"] if not r["inferred"]]
    assert len(explicit) == 1
    inferred = [r for r in got["transition_ledger"] if r["inferred"]]
    assert len(inferred) == 0


def test_eta_interleaved_triple_object_mesh() -> None:
    """Three units with staggered cross-channel sightings produce independent acyclic chains."""
    meta = json.loads((APP / "cases" / "eta" / "meta.json").read_text(encoding="utf-8"))
    got = _assert_pack_matches_reference(APP / "cases" / "eta")
    by_obj: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in got["transition_ledger"]:
        by_obj[row["object"]].append(row)
    assert set(by_obj.keys()) == set(meta["initial_holders"].keys())
    for rows in by_obj.values():
        rows.sort(key=lambda r: r["tick"])
        for i in range(1, len(rows)):
            assert rows[i - 1]["to"] == rows[i]["from"]
            assert rows[i]["tick"] >= rows[i - 1]["tick"]
        assert len(rows) >= 2
    assert got["consistency_proof"]["contradiction_resolved"] >= 2
    assert got["consistency_proof"]["gap_fill_count"] >= 5


def test_iota_six_hop_inferred_chain() -> None:
    """Sparse alternating channels require a long inferred movement chain for one unit."""
    meta = json.loads((APP / "cases" / "iota" / "meta.json").read_text(encoding="utf-8"))
    obj = next(iter(meta["initial_holders"]))
    got = _assert_pack_matches_reference(APP / "cases" / "iota")
    chain = [r for r in got["transition_ledger"] if r["object"] == obj]
    assert len(chain) == 5
    assert all(r["inferred"] for r in chain)
    assert got["consistency_proof"]["gap_fill_count"] == 5
    ticks = [r["tick"] for r in chain]
    assert ticks == sorted(ticks)
    assert chain[0]["from"] == meta["initial_holders"][obj]
    assert chain[-1]["tick"] == 11


def test_kappa_equal_rank_lex_channel_break() -> None:
    """When ranks tie, the lexicographically later channel id decides the merged sighting."""
    got = _assert_pack_matches_reference(APP / "cases" / "kappa")
    assert got["consistency_proof"]["contradiction_resolved"] == 1
    mid = [r for r in got["transition_ledger"] if r["tick"] == 6]
    assert len(mid) == 1
    assert mid[0]["inferred"] is True


def test_stutter_see_same_holder_emits_no_spurious_rows() -> None:
    """Repeated sightings of the same holder must not create extra ledger rows."""
    with tempfile.TemporaryDirectory() as tmp:
        pack_dir = _write_pack_dir(
            Path(tmp),
            "stutter-v",
            {"unit-s": "shelf-1"},
            {
                "north": "see 2 unit-s shelf-1\nsee 4 unit-s shelf-1\nsee 9 unit-s shelf-2\n",
                "gate": "see 3 unit-s shelf-1\nsee 7 unit-s shelf-2\n",
            },
        )
        ref = _reference_pack(pack_dir, _load_ranks())
        got = _assert_pack_matches_reference(pack_dir)
        assert len(got["transition_ledger"]) == 1
        assert got["transition_ledger"] == ref["transition_ledger"]
        assert got["consistency_proof"]["gap_fill_count"] == 1


def test_hidden_grading_mesh_nine_object_contradiction_grid() -> None:
    """Grading-style inline pack: dense multi-unit grid with contradictions and mixed verbs."""
    with tempfile.TemporaryDirectory() as tmp:
        pack_dir = _write_pack_dir(
            Path(tmp),
            "mesh-9",
            {
                "unit-a": "dock-a",
                "unit-b": "dock-b",
                "unit-c": "dock-c",
            },
            {
                "north": "\n".join(
                    [
                        "see 2 unit-a dock-a",
                        "see 5 unit-a bay-a",
                        "see 4 unit-b dock-b",
                        "xfer 6 unit-b dock-b lane-b",
                        "see 8 unit-b lane-b",
                        "see 3 unit-c dock-c",
                        "see 7 unit-c vault-c",
                    ]
                ),
                "gate": "\n".join(
                    [
                        "see 5 unit-a vault-a",
                        "see 6 unit-b dock-b",
                        "see 7 unit-c vault-x",
                    ]
                ),
                "yard": "\n".join(
                    [
                        "see 9 unit-a terminal-a",
                        "see 10 unit-c vault-c",
                    ]
                ),
            },
        )
        got = _assert_pack_matches_reference(pack_dir)
        assert got["consistency_proof"]["contradiction_resolved"] >= 2
        assert got["consistency_proof"]["gap_fill_count"] >= 3
        assert sum(1 for r in got["transition_ledger"] if not r["inferred"]) >= 1
        assert got["consistency_proof"]["ledger_digest"] == _digest_ledger(got["transition_ledger"])


def test_multi_xfer_back_to_back_explicit_rows() -> None:
    """Two explicit handoffs for one unit must both appear without inferred duplicates."""
    with tempfile.TemporaryDirectory() as tmp:
        pack_dir = _write_pack_dir(
            Path(tmp),
            "xfer-pair",
            {"unit-t": "base-0"},
            {
                "north": "\n".join(
                    [
                        "see 1 unit-t base-0",
                        "xfer 4 unit-t base-0 mid-1",
                        "xfer 8 unit-t mid-1 mid-2",
                        "see 12 unit-t mid-2",
                    ]
                ),
            },
        )
        ref = _reference_pack(pack_dir, _load_ranks())
        got = _assert_pack_matches_reference(pack_dir)
        explicit = [r for r in got["transition_ledger"] if not r["inferred"]]
        assert len(explicit) == 2
        assert explicit == [r for r in ref["transition_ledger"] if not r["inferred"]]
        assert got["consistency_proof"]["gap_fill_count"] == 0


def test_contradiction_burst_across_ticks_accumulates() -> None:
    """Multiple same-tick conflicts on different ticks each increment contradiction_resolved."""
    with tempfile.TemporaryDirectory() as tmp:
        pack_dir = _write_pack_dir(
            Path(tmp),
            "burst-c",
            {"unit-u": "start-u"},
            {
                "north": "see 3 unit-u hold-n1\nsee 8 unit-u hold-n2\n",
                "gate": "see 3 unit-u hold-g1\nsee 8 unit-u hold-g2\n",
                "yard": "see 3 unit-u hold-y1\nsee 8 unit-u hold-y2\n",
            },
        )
        ref = _reference_pack(pack_dir, _load_ranks())
        got = _assert_pack_matches_reference(pack_dir)
        assert got["consistency_proof"]["contradiction_resolved"] == 2
        assert len(got["transition_ledger"]) == len(ref["transition_ledger"])
        assert len([r for r in got["transition_ledger"] if r["tick"] == 8]) == 1


def test_digest_flips_when_inferred_bit_changes() -> None:
    """ledger_digest must incorporate the inferred boolean, not just movement endpoints."""
    sample = [
        {"tick": 4, "object": "unit-d", "from": "a", "to": "b", "inferred": True},
    ]
    flipped = [{**sample[0], "inferred": False}]
    assert _digest_ledger(sample) != _digest_ledger(flipped)
    with tempfile.TemporaryDirectory() as tmp:
        pack_dir = _write_pack_dir(
            Path(tmp),
            "digest-v",
            {"unit-d": "a"},
            {"north": "see 2 unit-d a\nsee 4 unit-d b\n"},
        )
        got = _assert_pack_matches_reference(pack_dir)
        assert got["transition_ledger"][0]["inferred"] is True
        assert got["consistency_proof"]["ledger_digest"] == _digest_ledger(got["transition_ledger"])
