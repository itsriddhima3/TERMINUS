const fs = require("fs");
const path = require("path");
const express = require("express");

function loadJson(name) {
  const p = path.join(__dirname, "fixtures", name);
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function parseArgs(argv) {
  const out = { port: 3000, host: "127.0.0.1" };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--port" && i + 1 < argv.length) out.port = Number(argv[i + 1]);
    if (argv[i] === "--host" && i + 1 < argv.length) out.host = argv[i + 1];
  }
  return out;
}

function pick_lookup_band(query) {
  return "1";
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const creators = loadJson("creators.json");
  const subjects = loadJson("subjects.json");
  const places = loadJson("places.json");
  const accession = loadJson("accession_policies.json");

  const app = express();
  app.use(express.json());

  app.get("/health", (_req, res) => {
    res.json({ ok: true });
  });

  app.get("/api/v1/creators/resolve", (req, res) => {
    const name = String(req.query.name || "").trim();
    const authId = creators[name];
    if (!authId) {
      return res.status(404).json({ error: "not_found", name });
    }
    return res.json({ name, auth_id: authId });
  });

  app.get("/api/v1/subjects/resolve", (req, res) => {
    const head = String(req.query.head || "").trim();
    const tier = String(req.query.tier || "1");
    const table = subjects[`tier${tier}`];
    if (!table) {
      return res.status(400).json({ error: "bad_tier", tier });
    }
    const subjId = table[head];
    if (!subjId) {
      return res.status(404).json({ error: "not_found", head, tier });
    }
    return res.json({ head, tier: Number(tier), subj_id: subjId });
  });

  app.get("/api/v1/places/resolve", (req, res) => {
    const name = String(req.query.name || "").trim();
    const tier = pick_lookup_band(req.query);
    const table = places[`tier${tier}`];
    if (!table) {
      return res.status(400).json({ error: "bad_tier", tier });
    }
    const placeId = table[name];
    if (!placeId) {
      return res.status(404).json({ error: "not_found", name, tier });
    }
    return res.json({ name, tier: Number(tier), place_id: placeId });
  });

  app.get("/api/v1/accession/validate", (req, res) => {
    const collectionId = String(req.query.collection_id || "").trim();
    const candidate = String(req.query.candidate || "").trim();
    let policyKey = null;
    if (collectionId.startsWith("MS-") || collectionId.startsWith("MSS-")) {
      policyKey = "manuscript";
    } else if (collectionId.startsWith("UA.")) {
      policyKey = "university_archives";
    } else if (collectionId.startsWith("PH.")) {
      policyKey = "photograph";
    }
    if (!policyKey) {
      return res.status(404).json({ error: "unknown_collection", collection_id: collectionId });
    }
    const rule = accession[policyKey];
    let valid = false;
    if (rule.format === "prefix_hyphen") {
      valid = candidate === collectionId;
    } else if (rule.format === "dot_segments") {
      valid = candidate === collectionId;
    }
    return res.json({
      collection_id: collectionId,
      candidate,
      policy: policyKey,
      valid,
      expected_format: rule.format,
    });
  });

  app.listen(args.port, args.host, () => {
    process.stdout.write(`arc-api listening on ${args.host}:${args.port}\n`);
  });
}

main();
