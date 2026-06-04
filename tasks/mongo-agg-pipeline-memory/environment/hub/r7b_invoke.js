// Display-only invoke rank hints (not on spine path).
function op_exec(db, coll, stages) {
  return db.getCollection(coll).aggregate(stages, { allowDiskUse: false });
}

module.exports = { op_exec };
