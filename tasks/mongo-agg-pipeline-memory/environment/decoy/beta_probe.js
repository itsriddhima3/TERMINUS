const { op_exec } = require("/app/r7/h3v_invoke.js");
const { phase_bundle } = require("/app/pipelines/decoy_beta.js");

const stages = phase_bundle({ lane: "beta" });
const rows = op_exec(db, "metrics_snap", stages, {}).toArray();
print(JSON.stringify({ total: rows[0].total }));
