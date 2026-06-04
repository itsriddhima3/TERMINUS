db = db.getSiblingDB("telemetry_db");
db.pipeline_meta.insertOne({
  marker: "v1",
  note: "baseline spine rollout",
  at: new Date(0),
});
