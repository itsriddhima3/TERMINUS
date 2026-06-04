const fs = require("fs");
const crypto = require("crypto");
const { allowDiskEnabled } = require("/app/app/audit_spill.js");
const { phase_bundle } = require("/app/x9/p9a_bundle.js");
const { op_exec } = require("/app/r7/h3v_invoke.js");

const matrix = JSON.parse(
  fs.readFileSync("/app/data/workload_matrix.json", "utf8")
);
const label = "WK-SPINE-EMEA";
const bands = matrix.workloads[label];
const cfg = {
  region: bands.filter_region,
  eventType: bands.filter_event_type,
};

const stages = phase_bundle(cfg);
const coll = db.getCollection(bands.spine_collection);

function stageKind(stage) {
  if (stage.$match) return "match";
  if (stage.$group) return "group";
  if (stage.$sort) return "sort";
  return "other";
}

let memory_limit_exceeded = false;
let rows = [];
try {
  const cursor = op_exec(db, bands.spine_collection, stages, {});
  rows = cursor.toArray();
} catch (err) {
  const msg = String(err.message || err);
  if (msg.includes("memory limit") || msg.includes("169")) {
    memory_limit_exceeded = true;
  } else {
    throw err;
  }
}

const firstKind = stages.length ? stageKind(stages[0]) : "other";
let examined = 0;
const returned = rows.length;
if (firstKind === "match") {
  examined = coll.countDocuments({
    region: bands.filter_region,
    event_type: bands.filter_event_type,
  });
} else {
  examined = coll.estimatedDocumentCount();
}

const ratio =
  returned > 0 ? examined / returned : examined > 0 ? examined : 0.0;

const allow_disk_enabled = allowDiskEnabled();

const pipeline_hash = crypto
  .createHash("sha256")
  .update(JSON.stringify(stages))
  .digest("hex");

const report = {
  schema_version: matrix.schema_version,
  workload_label: label,
  spine_collection: bands.spine_collection,
  filter_region: bands.filter_region,
  filter_event_type: bands.filter_event_type,
  result_total: rows.length ? rows[0].total : 0,
  grouped_keys: rows.length,
  memory_limit_exceeded,
  allow_disk_enabled,
  first_stage_kind: stages.length ? stageKind(stages[0]) : "other",
  match_stage_index: stages.findIndex((s) => stageKind(s) === "match"),
  examined_to_returned_ratio: ratio,
  pipeline_hash,
};

fs.writeFileSync(
  "/app/output/pipeline_audit.json",
  JSON.stringify(report, null, 2) + "\n"
);
print("AUDIT_OK");
