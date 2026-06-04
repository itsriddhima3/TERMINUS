db = db.getSiblingDB("telemetry_db");
db.pipeline_meta.insertOne({
  marker: "x9",
  note: "decoy hourly lane",
  lane: "beta",
});
