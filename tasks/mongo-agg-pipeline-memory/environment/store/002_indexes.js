// Index definitions for spine workloads.
db = db.getSiblingDB("telemetry_db");
db.events.createIndex({ region: 1, event_type: 1, seq: 1 });
db.events.createIndex({ shard_id: 1 });
db.metrics_snap.createIndex({ lane: 1 });
