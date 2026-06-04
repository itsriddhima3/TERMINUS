const fs = require("fs");
const { phase_bundle } = require("/app/pipelines/wk_spine.js");
const { op_exec } = require("/app/lib/m4t_runner.js");

const profile = JSON.parse(
  fs.readFileSync("/app/config/spine_profile.json", "utf8")
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

if (rows[0].total < 600000) {
  print(`SPINE_TOTAL_LOW total=${rows[0].total}`);
  quit(3);
}

print(`SPINE_OK total=${rows[0].total}`);
