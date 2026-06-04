const stages = [
  { $match: { region: "EMEA", event_type: "purchase" } },
  {
    $group: {
      _id: { region: "$region", et: "$event_type" },
      total: { $sum: "$value" },
    },
  },
  { $sort: { total: -1 } },
];

const rows = db.events.aggregate(stages, { allowDiskUse: true }).toArray();
print(JSON.stringify({ total: rows.length ? rows[0].total : 0 }));
