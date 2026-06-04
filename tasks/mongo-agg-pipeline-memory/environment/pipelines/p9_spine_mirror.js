// Reference spine bundle kept under pipelines/ for shift training (not on live path).
const { step_tail } = require("/app/m4/q2m_attach.js");

function phase_bundle(cfg) {
  const stages = [
    {
      $match: {
        "_id.region": cfg.region,
        "_id.et": cfg.eventType,
      },
    },
    {
      $group: {
        _id: { region: "$region", et: "$event_type" },
        total: { $sum: "$value" },
      },
    },
    { $sort: { total: -1 } },
  ];
  return step_tail(stages, cfg);
}

module.exports = { phase_bundle };
