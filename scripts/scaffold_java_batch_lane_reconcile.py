#!/usr/bin/env python3
"""One-shot scaffold for tasks/java-batch-lane-reconcile (Step 2b)."""
from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tasks" / "java-batch-lane-reconcile"
ENV = ROOT / "environment"

SCENARIO_ORDER = [
    "w1_single",
    "w2_pair",
    "w4_quad",
    "mix_parallel",
    "deplete_exact",
    "pipe_backlog",
    "idempotent_rerun",
    "over_cap_reject",
    "interleave_ab",
    "partial_abort",
    "stamp_guard",
    "post_write_snap",
    "sibling_contention",
    "pool_dual_conn",
    "parity_probe",
    "biz_key_race",
    "rollup_seq_m",
    "rollup_seq_n",
    "rollup_seq_o",
    "rollup_seq_p",
    "tri_fanout",
    "solo_west",
]

SCRIPT_LETTERS = list("abcdefghijklmnopqrstuv")


def w(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")


def main() -> None:
    w("instruction.md", INSTRUCTION)
    w("task.toml", TASK_TOML)
    w("output_contract.toml", OUTPUT_CONTRACT)
    w("tests/test.sh", TEST_SH)
    w("tests/test_outputs.py", TEST_OUTPUTS)
    w("solution/solve.sh", SOLVE_SH)
    w("solution/lane-fix.patch", LANE_FIX_PATCH)

    for d in [
        "environment/platform",
        "environment/init",
        "environment/db/migration",
        "environment/db/functions",
        "environment/api/src/main/java/k7m",
        "environment/api/src/main/java/r8p/entity",
        "environment/api/src/main/java/r8p/repo",
        "environment/api/src/main/java/r8p/event",
        "environment/api/src/main/java/decoy",
        "environment/api/src/main/resources",
        "environment/app",
        "environment/lib",
        "environment/data",
        "environment/config",
        "environment/docs/boundary_contract",
        "environment/decoy",
    ]:
        (ROOT / d).mkdir(parents=True, exist_ok=True)

    w("environment/.dockerignore", DOCKERIGNORE)
    w("environment/Dockerfile", DOCKERFILE)
    w("environment/platform/verifier-requirements.txt", "pytest==8.4.1\npytest-json-ctrf==0.3.5\n")

    for name, body in INIT_FILES.items():
        w(f"environment/init/{name}", body)

    for name, body in DB_FILES.items():
        w(f"environment/db/{name}", body)

    for name, body in API_FILES.items():
        w(f"environment/api/{name}", body)

    for name, body in LIB_FILES.items():
        w(f"environment/lib/{name}", body)

    w("environment/data/partition_catalog.json", PARTITION_CATALOG)
    w("environment/data/scenario_matrix.json", SCENARIO_MATRIX)
    w("environment/config/worker_policy.toml", WORKER_POLICY)

    for name, body in DOC_FILES.items():
        w(f"environment/docs/{name}", body)

    w("environment/decoy/n8f_metrics.sql", DECOY_SQL)
    w("environment/app/lane_audit.sh", LANE_AUDIT)

    for letter, key in zip(SCRIPT_LETTERS, SCENARIO_ORDER):
        w(f"environment/app/scenario_{letter}.sh", scenario_script(letter, key))

    print(f"Scaffolded {ROOT}")


INSTRUCTION = """\
Our Spring Boot chunk ingest service at `/app` loses rows and duplicates business keys when we run parallel uploads on North-Shelf (six active slots), East-Crate (ten), or West-Bin (four). Single-threaded replays on those families still look fine.

Run `/app/app/lane_audit.sh` and read `/app/output/lane_audit.json` — that report is how we will judge the fix. Each scenario row should end with `lost_rows` 0, `duplicate_external_keys` 0, `unstable_totals` false, and `ingest_compliance` true. The `stress_summary` block should report zero loss events when the full matrix is clean.

The playbooks under `/app/docs/` blame database tuning, but QA thinks we are breaking several invariants at once. If the boundary material under `/app/docs/boundary_contract/` disagrees with a playbook, follow the boundary spec; `/app/docs/bench_precedence.md` says how to resolve that conflict.
"""

TASK_TOML = """\
version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "debugging"
subcategories = ["db_interaction", "tool_specific", "long_context"]
number_of_milestones = 0
codebase_size = "small"
languages = ["java", "sql", "bash"]
tags = ["java", "spring", "postgresql", "jpa", "concurrency"]
expert_time_estimate_min = 120
junior_time_estimate_min = 480

[agent]
timeout_sec = 1800.0

[verifier]
timeout_sec = 900.0

[environment]
build_timeout_sec = 900.0
cpus = 2
memory_mb = 6144
storage_mb = 10240
workdir = "/app"
allow_internet = false
"""

OUTPUT_CONTRACT = """\
user_visible_outputs = ["/app/output/lane_audit.json"]

internal_harness_files = [
  "/app/app/lane_audit.sh",
  "/app/data/scenario_matrix.json",
  "/app/data/partition_catalog.json",
  "/app/init/start_api.sh",
]

[structured_outputs.lane_audit]
target = "/app/output/lane_audit.json"
format = "json"
instruction_checks = [
  "schema_version",
  "catalog_partitions",
  "scenarios",
  "ingest_compliance",
  "lost_rows",
  "duplicate_external_keys",
  "unstable_totals",
  "stress_summary",
  "lane_audit.json",
]
"""

TEST_SH = """\
#!/bin/bash

# Offline verifier: Dockerfile warms pytest into /opt/uv-cache; UV_OFFLINE=1 at runtime.
source $HOME/.local/bin/env

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
    exit 1
fi

uvx \
  -p 3.13 \
  -w pytest==8.4.1 \
  -w pytest-json-ctrf==0.3.5 \
  pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
"""

# test_outputs.py and remaining blobs appended in next write via exec

if __name__ == "__main__":
    # Import heavy content from companion module when present
    try:
        from scaffold_java_batch_lane_content import *  # noqa: F403
    except ImportError:
        pass
    main()
