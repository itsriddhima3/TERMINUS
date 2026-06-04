const fs = require("fs");
const path = require("path");
const Fastify = require("fastify");

function loadJson(name) {
  const p = path.join(__dirname, "fixtures", name);
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function parseArgs(argv) {
  const out = { port: 3921, host: "127.0.0.1" };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--port" && i + 1 < argv.length) out.port = Number(argv[i + 1]);
    if (argv[i] === "--host" && i + 1 < argv.length) out.host = argv[i + 1];
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const tariffs = loadJson("tariffs.json");
  const fx = loadJson("fx.json");
  const quotas = loadJson("quotas.json");

  const app = Fastify({ logger: false });

  app.get("/health", async () => ({ ok: true }));

  app.get("/api/v1/tariff/:hs10", async (req, reply) => {
    const hs10 = String(req.params.hs10 || "");
    const row = tariffs[hs10];
    if (!row) {
      return reply.code(404).send({ error: "not_found", hs10 });
    }
    return { hs10, rate_pct: row.rate_pct };
  });

  app.get("/api/v1/fx/:ccy", async (req, reply) => {
    const ccy = String(req.params.ccy || "").toUpperCase();
    const factor = fx[ccy];
    if (factor === undefined) {
      return reply.code(404).send({ error: "not_found", currency: ccy });
    }
    return { currency: ccy, fx_to_usd: factor };
  });

  app.get("/api/v1/quota/:hs10", async (req, reply) => {
    const hs10 = String(req.params.hs10 || "");
    const row = quotas[hs10];
    if (!row) {
      return reply.code(404).send({ error: "not_found", hs10 });
    }
    return { hs10, blocked: row.blocked };
  });

  function loadBatchLines(batchId) {
    const csvPath = path.join(__dirname, "..", "data", "shipments", `${batchId}.csv`);
    if (!fs.existsSync(csvPath)) {
      return null;
    }
    const rows = [];
    for (const line of fs.readFileSync(csvPath, "utf8").trim().split("\n").slice(1)) {
      const [lineId, importerId, hsRaw, currencyRaw, declaredValue, declaredDuty] =
        line.split(",");
      rows.push({
        line_id: lineId,
        importer_id: importerId,
        hs_raw: hsRaw,
        currency_raw: currencyRaw,
        declared_value: Number(declaredValue),
        declared_duty: Number(declaredDuty),
      });
    }
    return rows;
  }

  app.get("/api/v1/batch/:batchId", async (req, reply) => {
    const batchId = String(req.params.batchId || "");
    const lines = loadBatchLines(batchId);
    if (!lines) {
      return reply.code(404).send({ error: "not_found", batch_id: batchId });
    }
    return {
      batch_id: batchId,
      lines,
      legacy_rows: [],
    };
  });

  await app.listen({ port: args.port, host: args.host });
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
