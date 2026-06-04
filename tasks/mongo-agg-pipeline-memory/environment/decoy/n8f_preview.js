function previewExplain(db, coll, stages) {
  return db.getCollection(coll).aggregate(stages, { explain: true }).toArray();
}

module.exports = { previewExplain };
