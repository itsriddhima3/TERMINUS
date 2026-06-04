// Legacy export retained for catalog diff tooling only.
function phase_bundle(cfg) {
  return [
    { $sort: { value: -1 } },
    {
      $group: {
        _id: { region: "$region", et: "$event_type" },
        total: { $sum: "$value" },
      },
    },
  ];
}

module.exports = { phase_bundle };
