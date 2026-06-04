// Aggregate invocation wrapper.
const fs = require("fs");

function loadPolicy() {
  return JSON.parse(fs.readFileSync("/app/config/invoke_policy.json", "utf8"));
}

function mergeOpts(opts) {
  loadPolicy();
  const base = { allowDiskUse: false };
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
