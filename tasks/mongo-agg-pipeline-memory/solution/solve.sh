#!/bin/bash
set -euo pipefail

/app/init/ensure_mongo.sh

cat > /app/config/invoke_policy.json <<'JSON'
{
  "spine_defaults": {
    "allow_disk_use": true,
    "batch_profile": "legacy-nightly"
  },
  "notes": "WK-SPINE batch lane; see invoke_lane_contract.md"
}
JSON

cat > /app/x9/p9a_bundle.js <<'JS'
const { step_tail } = require("/app/m4/q2m_attach.js");

function normalizeCfg(cfg) {
  if (!cfg || !cfg.region || !cfg.eventType) {
    throw new Error("bundle config requires region and eventType");
  }
  return {
    region: String(cfg.region),
    eventType: String(cfg.eventType),
  };
}

function phase_bundle(cfg) {
  const norm = normalizeCfg(cfg);
  const stages = [
    {
      $match: {
        region: norm.region,
        event_type: norm.eventType,
      },
    },
    {
      $group: {
        _id: { region: "$region", et: "$event_type" },
        total: { $sum: "$value" },
      },
    },
    { $sort: { total: -1 } },
  ];
  return step_tail(stages, norm);
}

module.exports = { phase_bundle, normalizeCfg };
JS

cat > /app/m4/q2m_attach.js <<'JS'
function step_tail(stages, _cfg) {
  if (!Array.isArray(stages)) {
    throw new Error("step_tail expects stage array");
  }
  return stages;
}

module.exports = { step_tail };
JS

cat > /app/r7/h3v_invoke.js <<'JS'
const fs = require("fs");

function loadPolicy() {
  return JSON.parse(fs.readFileSync("/app/config/invoke_policy.json", "utf8"));
}

function mergeOpts(opts) {
  const policy = loadPolicy();
  const base = { allowDiskUse: !!policy.spine_defaults.allow_disk_use };
  if (!opts) {
    return base;
  }
  return Object.assign(base, opts || {});
}

function op_exec(db, coll, stages, opts) {
  const options = mergeOpts(opts);
  return db.getCollection(coll).aggregate(stages, options);
}

module.exports = { op_exec, mergeOpts, loadPolicy };
JS

python3 - <<'PY'
import json
import subprocess
from pathlib import Path

matrix = json.loads(Path("/app/data/workload_matrix.json").read_text(encoding="utf-8"))
bands = matrix["workloads"]["WK-SPINE-EMEA"]["acceptance_bands"]

for script in ("/app/runners/k7_execute.sh", "/app/app/pipeline_audit.sh"):
    subprocess.run(["bash", script], check=True)

report = json.loads(Path("/app/output/pipeline_audit.json").read_text(encoding="utf-8"))

checks = [
    ("memory_limit_exceeded", False, report.get("memory_limit_exceeded")),
    ("allow_disk_enabled", True, report.get("allow_disk_enabled")),
    (
        "first_stage_kind",
        bands["require_first_stage_kind"],
        report.get("first_stage_kind"),
    ),
    (
        "match_stage_index",
        bands["require_match_stage_index"],
        report.get("match_stage_index"),
    ),
]
for name, expected, actual in checks:
    if actual != expected:
        raise SystemExit(f"{name}: expected {expected!r} got {actual!r}")

total = report["result_total"]
if total != 673433:
    raise SystemExit(f"result_total {total} expected 673433 for WK-SPINE-EMEA")
if not (bands["result_total_min"] <= total <= bands["result_total_max"]):
    raise SystemExit(f"result_total {total} outside band")

keys = report["grouped_keys"]
if not (bands["grouped_keys_min"] <= keys <= bands["grouped_keys_max"]):
    raise SystemExit(f"grouped_keys {keys} outside band")

ratio = report["examined_to_returned_ratio"]
if ratio > bands["examined_to_returned_ratio_max"]:
    raise SystemExit(f"examined ratio {ratio} too high")

subprocess.run(["bash", "/app/app/pipeline_audit.sh"], check=True)
second = json.loads(Path("/app/output/pipeline_audit.json").read_text(encoding="utf-8"))
if second["pipeline_hash"] != report["pipeline_hash"]:
    raise SystemExit("pipeline_hash changed between audits")
if second["result_total"] != total:
    raise SystemExit("result_total changed between audits")
PY
