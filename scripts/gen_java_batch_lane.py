#!/usr/bin/env python3
"""Generate tasks/java-batch-lane-reconcile environment + solution + tests."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tasks" / "java-batch-lane-reconcile"
ENV = ROOT / "environment"

SCENARIO_ORDER = [
    "w1_single", "w2_pair", "w4_quad", "mix_parallel", "deplete_exact", "pipe_backlog",
    "idempotent_rerun", "over_cap_reject", "interleave_ab", "partial_abort", "stamp_guard",
    "post_write_snap", "sibling_contention", "pool_dual_conn", "parity_probe", "biz_key_race",
    "rollup_seq_m", "rollup_seq_n", "rollup_seq_o", "rollup_seq_p", "tri_fanout", "solo_west",
]
LETTERS = list("abcdefghijklmnopqrstuv")


def w(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    text = content if content.endswith("\n") else content + "\n"
    p.write_text(text, encoding="utf-8")


def main() -> None:
    w("construction_manifest.json", CONSTRUCTION_MANIFEST)
    w("tests/test_outputs.py", TEST_OUTPUTS)
    w("solution/solve.sh", SOLVE_SH)
    w("solution/lane-fix.patch", LANE_FIX_PATCH)

    for sub in [
        "environment/platform", "environment/init", "environment/db/migration",
        "environment/db/functions", "environment/api/src/main/java/k7m",
        "environment/api/src/main/java/r8p/entity", "environment/api/src/main/java/r8p/repo",
        "environment/api/src/main/java/r8p/event", "environment/api/src/main/java/r8p/dto",
        "environment/api/src/main/java/decoy", "environment/api/src/main/resources",
        "environment/app", "environment/lib", "environment/data", "environment/config",
        "environment/docs/boundary_contract", "environment/decoy",
    ]:
        (ROOT / sub).mkdir(parents=True, exist_ok=True)

    files = {
        "environment/.dockerignore": DOCKERIGNORE,
        "environment/Dockerfile": DOCKERFILE,
        "environment/platform/verifier-requirements.txt": "pytest==8.4.1\npytest-json-ctrf==0.3.5\n",
        **{f"environment/init/{k}": v for k, v in INIT.items()},
        **{f"environment/db/{k}": v for k, v in DB.items()},
        **{f"environment/api/{k}": v for k, v in API.items()},
        **{f"environment/lib/{k}": v for k, v in LIB.items()},
        "environment/data/partition_catalog.json": PARTITION_CATALOG,
        "environment/data/scenario_matrix.json": SCENARIO_MATRIX,
        "environment/config/worker_policy.toml": WORKER_POLICY,
        **{f"environment/docs/{k}": v for k, v in DOCS.items()},
        "environment/decoy/n8f_metrics.sql": DECOY_SQL,
        "environment/app/lane_audit.sh": LANE_AUDIT,
    }
    for rel, body in files.items():
        w(rel, body)

    for letter, key in zip(LETTERS, SCENARIO_ORDER):
        w(f"environment/app/scenario_{letter}.sh", scenario_sh(letter, key))

    print(f"Generated under {ROOT}")


def scenario_sh(letter: str, key: str) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
source /app/lib/curl_wrap.sh
source /app/lib/result_collect.sh
exec /app/lib/run_scenario.sh "{key}"
"""


CONSTRUCTION_MANIFEST = json.dumps(
    {
        "symbol_table": [
            {
                "path": "environment/api/src/main/java/r8p/op_n2.java",
                "symbol": "op_n2",
                "kind": "method",
                "signature": "public IngestResult op_n2(String label, List<RowPayload> chunk)",
                "purpose": "persists a chunked ingest for a catalog label with flush boundaries",
            },
            {
                "path": "environment/api/src/main/java/r8p/phase_r8.java",
                "symbol": "phase_r8",
                "kind": "class",
                "signature": "@Component class phase_r8 implements ApplicationListener<LaneCommittedEvent>",
                "purpose": "schedules follow-up work when a lane chunk reports success",
            },
            {
                "path": "environment/db/functions/step_w1.sql",
                "symbol": "step_w1",
                "kind": "function",
                "signature": "step_w1() RETURNS trigger LANGUAGE plpgsql",
                "purpose": "maintains partition rollup counters on line mutations",
            },
            {
                "path": "environment/api/src/main/java/k7m/cfg_p9.java",
                "symbol": "cfg_p9",
                "kind": "constant",
                "signature": "@Bean HikariDataSource cfg_p9(DataSourceProperties props)",
                "purpose": "builds the runtime pool with session initializer hooks",
            },
        ],
        "flipping_point_contract": {
            "locations": [
                {
                    "id": "A",
                    "path": "environment/api/src/main/java/r8p/op_n2.java",
                    "controls_tests": [
                        "test_w2_pair", "test_w4_quad", "test_backlog_ok", "test_mix_ok",
                        "test_global_ok", "test_interleave_ab", "test_partial_abort_ok",
                        "test_line_parity_matrix", "test_race_one_winner",
                        "test_snapshot_consistent", "test_tri_fanout_ok",
                    ],
                },
                {
                    "id": "B",
                    "path": "environment/api/src/main/java/r8p/phase_r8.java",
                    "controls_tests": [
                        "test_w1_single", "test_rerun_ok", "test_cap_reject", "test_no_loss",
                        "test_partial_abort_ok", "test_stamp_diverge_guard", "test_race_one_winner",
                    ],
                },
                {
                    "id": "C",
                    "path": "environment/db/functions/step_w1.sql",
                    "controls_tests": [
                        "test_deplete_ok", "test_label_order", "test_slots_complete",
                        "test_contention_sibling", "test_monotone_counter", "test_tri_fanout_ok",
                    ],
                },
                {
                    "id": "D",
                    "path": "environment/api/src/main/java/k7m/cfg_p9.java",
                    "controls_tests": [
                        "test_v1_field", "test_mix_ok", "test_snapshot_consistent",
                        "test_pool_handoff_ok", "test_tri_fanout_ok",
                    ],
                },
            ],
            "no_single_location_flips_majority": True,
            "concentration_cap": 0.5,
        },
        "decoy_manifest": [
            {
                "path": "environment/api/src/main/java/decoy/PessimisticAdvice.java",
                "kind": "module",
                "rhymes_with": "op_n2",
                "non_fix_purpose": "documents table-wide lock acquisition patterns referenced in operations notes",
            },
            {
                "path": "environment/api/src/main/java/decoy/BatchTuner.java",
                "kind": "module",
                "rhymes_with": "cfg_p9",
                "non_fix_purpose": "adjusts batch size and fetch depth for reporting queries only",
            },
            {
                "path": "environment/decoy/n8f_metrics.sql",
                "kind": "helper",
                "rhymes_with": "step_w1",
                "non_fix_purpose": "nightly rollup metrics snapshot not on ingest hot path",
            },
        ],
        "code_forbidden_tokens": [
            "spring", "boot", "chunk", "ingest", "service", "loses", "rows", "duplicates",
            "business", "keys", "whenever", "parallel", "uploads", "single-threaded", "replays",
            "north-shelf", "east-crate", "west-bin", "lane_audit", "read", "report", "judge",
            "playbooks", "database", "tuning", "qa", "thinks", "breaking", "several",
            "invariants", "boundary", "material", "disagrees", "playbook", "follow",
            "bench_precedence", "conflict", "need", "every", "scenario", "lost", "duplicate",
            "external", "stable", "rollup", "totals", "ingest_compliance", "fine", "still",
            "look", "stress_summary", "block", "should", "end", "those", "families",
        ],
    },
    indent=2,
) + "\n"

PARTITION_CATALOG = json.dumps(
    {
        "schema_version": 1,
        "partitions": [
            {"label": "North-Shelf", "cap_slots": 6},
            {"label": "East-Crate", "cap_slots": 10},
            {"label": "West-Bin", "cap_slots": 4},
        ],
    },
    indent=2,
) + "\n"

SCENARIO_MATRIX = json.dumps({"schema_version": 1, "scenario_order": SCENARIO_ORDER}, indent=2) + "\n"

WORKER_POLICY = """\
max_workers_per_family = 4
default_line_qty = 1
retry_budget = 2
snapshot_wait_ms = 80
"""

DOCKERIGNORE = """\
.git
.gitignore
**/__pycache__/
**/*.pyc
**/.pytest_cache/
**/target/
**/node_modules/
solution/
tests/
"""

# Continued in part 2 - imported at runtime
if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from gen_java_batch_lane_blobs import *  # noqa: F403, F401
    from gen_java_batch_lane_api import API, DOCS, TEST_OUTPUTS  # noqa: F401
    from gen_java_batch_lane_solve import LANE_FIX_PATCH, SOLVE_SH  # noqa: F401

    main()
