const { phase_bundle } = require("/app/pipelines/decoy_beta.js");
const { op_exec } = require("/app/r7/h3v_invoke.js");

function runBeta(db) {
  const stages = phase_bundle({ lane: "beta" });
  const cursor = op_exec(db, "metrics_snap", stages, {});
  return cursor.toArray();
}

module.exports = { runBeta };
