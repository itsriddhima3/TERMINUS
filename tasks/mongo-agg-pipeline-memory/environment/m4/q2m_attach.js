// Trailing predicate attachment for spine bundles.

function step_tail(stages, cfg) {
  return stages.concat([
    {
      $match: {
        region: cfg.region,
        event_type: cfg.event_type,
      },
    },
  ]);
}

module.exports = { step_tail };
