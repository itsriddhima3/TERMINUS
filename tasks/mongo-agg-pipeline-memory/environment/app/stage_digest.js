const { phase_bundle } = require("/app/x9/p9a_bundle.js");

const cfg = { region: "EMEA", eventType: "purchase" };
const stages = phase_bundle(cfg);

function stageKind(stage) {
  if (stage.$match) return "match";
  if (stage.$group) return "group";
  if (stage.$sort) return "sort";
  return "other";
}

let tail_document_match = false;
for (let i = 1; i < stages.length; i += 1) {
  const m = stages[i].$match;
  if (m && Object.prototype.hasOwnProperty.call(m, "region")) {
    tail_document_match = true;
  }
}

const first = stages[0] || {};
const firstMatch = first.$match || {};

print(
  JSON.stringify({
    stage_count: stages.length,
    first_stage_kind: stages.length ? stageKind(stages[0]) : "other",
    first_has_region: Object.prototype.hasOwnProperty.call(firstMatch, "region"),
    first_has_event_type: Object.prototype.hasOwnProperty.call(
      firstMatch,
      "event_type"
    ),
    tail_document_match,
  })
);
