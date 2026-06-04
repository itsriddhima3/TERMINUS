#!/usr/bin/env bash
set -euo pipefail

/app/init/ensure_pg.sh

mkdir -p /app/output

python3 - <<'PY'
import json
import subprocess
from pathlib import Path

catalog = json.loads(Path("/app/data/org_catalog.json").read_text())
matrix = json.loads(Path("/app/data/scenario_matrix.json").read_text())

scenario_scripts = {
    "adhoc_single": "/app/app/scenario_a.sh",
    "reuse_stmt": "/app/app/scenario_b.sh",
    "pool_rotate": "/app/app/scenario_c.sh",
    "join_path": "/app/app/scenario_d.sh",
    "view_path": "/app/app/scenario_e.sh",
    "batch_fetch": "/app/app/scenario_f.sh",
    "triple_hop": "/app/app/scenario_g.sh",
    "savepoint_cycle": "/app/app/scenario_h.sh",
    "nested_subquery": "/app/app/scenario_i.sh",
    "aggregate_reuse": "/app/app/scenario_j.sh",
    "cte_chain": "/app/app/scenario_k.sh",
    "inventory_lane": "/app/app/scenario_l.sh",
    "audit_log_chain": "/app/app/scenario_m.sh",
    "union_rotate": "/app/app/scenario_n.sh",
    "window_rank": "/app/app/scenario_o.sh",
    "reader_lane": "/app/app/scenario_p.sh",
    "warm_cache_first": "/app/app/scenario_r.sh",
    "dual_stmt_interleave": "/app/app/scenario_s.sh",
    "lateral_correlation": "/app/app/scenario_t.sh",
}


def pg_q(sql: str) -> str:
    r = subprocess.run(
        ["psql", "-U", "postgres", "-d", "saas_db", "-At", "-c", sql],
        text=True, capture_output=True, check=False,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "postgres query failed")
    return r.stdout.strip()


def policy_structure_ok() -> bool:
    """Return True when core-table row filters route through the session accessor."""
    rows = pg_q(
        "SELECT c.relname, pg_get_expr(p.polqual, p.polrelid) "
        "FROM pg_policy p JOIN pg_class c ON c.oid = p.polrelid "
        "WHERE c.relname IN ('ledger','contacts','inventory','audit_log') "
        "ORDER BY c.relname;"
    )
    for line in rows.splitlines():
        if not line.strip():
            continue
        _, expr = line.split("|", 1)
        if "current_setting(" in expr:
            return False
    return bool(rows.strip())


def accessor_class_ok() -> bool:
    """Return True when the session scope accessor is classified for per-statement re-evaluation."""
    return pg_q("SELECT provolatile FROM pg_proc WHERE proname='fn_k7';") == "v"


scenarios = {}
for name in matrix["scenario_order"]:
    script = scenario_scripts[name]
    if name == "adhoc_single":
        proc = subprocess.run([script], check=True, text=True, capture_output=True)
        parts = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
        merged = {
            "cross_scope_visible": any(p["cross_scope_visible"] for p in parts),
            "foreign_labels_seen": sorted({label for p in parts for label in p["foreign_labels_seen"]}),
            "owned_row_count": max(p["owned_row_count"] for p in parts),
        }
        scenarios[name] = merged
        continue
    proc = subprocess.run([script], check=True, text=True, capture_output=True)
    payload = proc.stdout.strip().splitlines()[-1]
    scenarios[name] = json.loads(payload)

report = {
    "schema_version": matrix["schema_version"],
    "catalog_labels": [row["label"] for row in catalog],
    "catalog_compliance": {
        "tenant_policies_use_accessor": policy_structure_ok(),
        "scope_accessor_volatile": accessor_class_ok(),
    },
    "scenarios": scenarios,
}

Path("/app/output/boundary_audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
PY
