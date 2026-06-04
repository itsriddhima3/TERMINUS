// Hourly beta rollup on metrics_snap (decoy path).

function phase_bundle(cfg) {
  return [
    { $match: { lane: cfg.lane || "beta" } },
    {
      $group: {
        _id: "$lane",
        total: { $sum: "$reading" },
      },
    },
  ];
}

module.exports = { phase_bundle };
