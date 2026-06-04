// Collection layout markers for telemetry_db.
db = db.getSiblingDB("telemetry_db");
db.createCollection("events");
db.createCollection("metrics_snap");
