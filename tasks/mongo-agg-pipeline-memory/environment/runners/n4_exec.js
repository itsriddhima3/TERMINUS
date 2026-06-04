const fs = require("fs");
const { phase_bundle } = require("/app/x9/p9a_bundle.js");
const { op_exec } = require("/app/r7/h3v_invoke.js");

const profile = JSON.parse(
  fs.readFileSync("/app/config/w9_profile.json", "utf8")
);
const matrix = JSON.parse(
  fs.readFileSync("/app/data/workload_matrix.json", "utf8")
);
const label = "WK-SPINE-EMEA";
const cfg = profile.workloads[label];
const bands = matrix.workloads[label];

const stages = phase_bundle({
  region: cfg.filter_region,
  eventType: cfg.filter_event_type,
});

let rows;
try {
  const cursor = op_exec(db, bands.spine_collection, stages, {});
  rows = cursor.toArray();
} catch (err) {
  print(`SPINE_RUN_ERROR: ${err.message}`);
  quit(1);
}

if (!rows.length) {
  print("SPINE_RUN_EMPTY");
  quit(2);
}

print(`SPINE_OK total=${rows[0].total}`);
