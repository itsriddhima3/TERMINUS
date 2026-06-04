#!/usr/bin/env bash
set -euo pipefail

source /app/lib/redis_wrap.sh
source /app/lib/seed_helpers.sh
source /app/worker/phase_r8.sh

mkdir -p /app/output

python3 - <<'PY'
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

APP = Path("/app")
catalog = json.loads((APP / "data/sku_catalog.json").read_text())
matrix = json.loads((APP / "data/scenario_matrix.json").read_text())
canonical = {row["label"]: row["key"] for row in catalog}
opening_map = {row["label"]: row["opening_units"] for row in catalog}


def redis_cmd(*args: str) -> str:
    r = subprocess.run(["redis-cli", *args], text=True, capture_output=True, check=False)
    if r.returncode != 0:
        raise RuntimeError(r.stderr or "redis-cli failed")
    return (r.stdout or "").strip()


def worker_slot(label: str) -> str:
    r = subprocess.run(["bash", "-c", f'source /app/lib/k7m/step_w1.sh; step_w1 "{label}"'],
                       text=True, capture_output=True, check=False)
    return r.stdout.strip()


def reset_label(label: str, opening: int) -> None:
    redis_cmd("SET", canonical[label], str(opening))


def phase_r8(label: str, qty: int) -> int:
    r = subprocess.run(
        ["bash", "/app/worker/phase_r8.sh", label, str(qty)],
        text=True, capture_output=True, check=False,
    )
    out = (r.stdout or "").strip()
    try:
        return int(out or "0")
    except ValueError:
        return 0


def run_workers(label: str, workers: int, qty: int, *, pipelined: bool = False, retries: int = 0) -> tuple[int, int, int]:
    opening = opening_map[label]
    reset_label(label, opening)
    slot = worker_slot(label)
    attempts = 0
    grants = 0

    def one_attempt() -> int:
        return phase_r8(label, qty)

    if pipelined:
        for _ in range(workers):
            attempts += 1
            grants += one_attempt()
    else:
        with ThreadPoolExecutor(max_workers=max(workers, 1)) as pool:
            futs = []
            for _ in range(workers):
                attempts += 1
                futs.append(pool.submit(one_attempt))
            for _ in range(retries):
                attempts += 1
                futs.append(pool.submit(one_attempt))
            for fut in as_completed(futs):
                grants += int(fut.result() or 0)

    final = int(redis_cmd("GET", slot) or "0")
    return grants, final, attempts


def run_bimodal(label: str, groups: list[dict], opening: int) -> tuple[int, int, int]:
    reset_label(label, opening)
    slot = worker_slot(label)
    grants = 0
    attempts = 0
    total_workers = sum(int(g["workers"]) for g in groups)
    with ThreadPoolExecutor(max_workers=max(total_workers, 1)) as pool:
        futs = []
        for group in groups:
            for _ in range(int(group["workers"])):
                attempts += 1
                futs.append(pool.submit(phase_r8, label, int(group["qty_each"])))
        for fut in as_completed(futs):
            grants += int(fut.result() or 0)
    final = int(redis_cmd("GET", slot) or "0")
    return grants, final, attempts


def run_two_phase(label: str, phases: list[dict], opening: int) -> tuple[int, int, int]:
    reset_label(label, opening)
    slot = worker_slot(label)
    grants = 0
    attempts = 0
    for phase in phases:
        workers = int(phase["workers"])
        qty = int(phase["qty_each"])
        with ThreadPoolExecutor(max_workers=max(workers, 1)) as pool:
            futs = [pool.submit(phase_r8, label, qty) for _ in range(workers)]
            for fut in as_completed(futs):
                attempts += 1
                grants += int(fut.result() or 0)
    final = int(redis_cmd("GET", slot) or "0")
    return grants, final, attempts


def run_mixed(pairs: list[dict]) -> tuple[int, int, int, bool]:
    """Return aggregate grants, min final stock, attempts, oversell flag."""
    total_grants = 0
    total_attempts = 0
    min_final = 10**9
    oversell = False
    for pair in pairs:
        label = pair["sku"]
        opening = pair["opening"]
        reset_label(label, opening)
    with ThreadPoolExecutor(max_workers=len(pairs) * 2) as pool:
        futs = []
        for pair in pairs:
            label = pair["sku"]
            workers = pair["workers"]
            qty = pair["qty_each"]
            for _ in range(workers):
                total_attempts += 1
                futs.append((label, opening_map[label], pool.submit(phase_r8, label, qty)))
        for label, opening, fut in futs:
            g = int(fut.result() or 0)
            total_grants += g
            slot = worker_slot(label)
            final = int(redis_cmd("GET", slot) or "0")
            min_final = min(min_final, final)
            if g > opening:
                oversell = True
            if final < 0:
                oversell = True
    return total_grants, min_final, total_attempts, oversell


def scenario_row(name: str, spec: dict) -> dict:
    if "pairs" in spec:
        grants, final, attempts, oversell_flag = run_mixed(spec["pairs"])
        opening = sum(p["opening"] for p in spec["pairs"])
        oversell = oversell_flag or grants > opening
        return {
            "oversell_detected": oversell,
            "total_granted": grants,
            "final_stock": final,
            "requests_attempted": attempts,
            "sku": "mixed" if len(spec["pairs"]) == 2 else "triple",
        }

    label = spec["sku"]
    opening = spec["opening"]

    if "phases" in spec:
        grants, final, attempts = run_two_phase(label, spec["phases"], opening)
    elif "bimodal" in spec:
        grants, final, attempts = run_bimodal(label, spec["bimodal"], opening)
    else:
        workers = spec["workers"]
        qty = spec["qty_each"]
        pipelined = bool(spec.get("pipelined"))
        retries = int(spec.get("retries", 0))
        grants, final, attempts = run_workers(
            label, workers, qty, pipelined=pipelined, retries=retries
        )

    oversell = grants > opening or final < 0
    return {
        "oversell_detected": oversell,
        "total_granted": grants,
        "final_stock": final,
        "requests_attempted": attempts,
        "sku": label,
    }


scenarios = {}
oversell_events = 0
for name, spec in matrix.items():
    row = scenario_row(name, spec)
    scenarios[name] = row
    if row["oversell_detected"]:
        oversell_events += 1

# structural compliance probes
slot_sample = worker_slot("Alpha-Unit")
canonical_sample = canonical["Alpha-Unit"]
uses_alias = slot_sample != canonical_sample

def read_forward_policy() -> bool:
    text = (APP / "config/worker_policy.toml").read_text()
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("forward_observation_frame"):
            _, _, val = line.partition("=")
            return val.strip().lower() in {"1", "true", "yes"}
    return False

report = {
    "schema_version": 1,
    "catalog_skus": [row["label"] for row in catalog],
    "scenarios": scenarios,
    "stock_compliance": {
        "canonical_keys_seeded": True,
        "worker_slot_is_alias": uses_alias,
        "forward_observation_frame": read_forward_policy(),
    },
    "stress_summary": {
        "oversell_events": oversell_events,
        "scenario_count": len(scenarios),
    },
}

Path("/app/output").mkdir(parents=True, exist_ok=True)
Path("/app/output/stock_audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
PY
