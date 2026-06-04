const fs = require("fs");

db = db.getSiblingDB("telemetry_db");

if (db.events.estimatedDocumentCount() === 0) {
  const raw = fs.readFileSync("/app/data/events_seed.ndjson", "utf8");
  const lines = raw.split("\n").filter((line) => line.trim());
  const batch = 5000;
  for (let i = 0; i < lines.length; i += batch) {
    const docs = lines.slice(i, i + batch).map((line) => JSON.parse(line));
    db.events.insertMany(docs, { ordered: false });
  }
}

if (db.metrics_snap.estimatedDocumentCount() === 0) {
  const snaps = [];
  for (let i = 0; i < 120; i += 1) {
    snaps.push({ lane: "beta", reading: (i % 7) + 1, seq: i });
  }
  db.metrics_snap.insertMany(snaps);
}

print("BOOTSTRAP_OK");
