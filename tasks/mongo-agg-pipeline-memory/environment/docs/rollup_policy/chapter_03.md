# Chapter 03 — Spine stage ordering

WK-SPINE bundles must apply selective predicates on **raw** `region` and `event_type` fields before any `$group` or `$sort` stage materializes the full events store.

Matching on `_id.region` or `_id.et` after grouping is a post-accumulator filter only; it does not reduce working-set size for blocking stages.

Reference bundles under `/app/pipelines/` may show alternate ordering for training; the live runner imports bundle code from `/app/x9/`.

With tail attachment neutralized, the live WK-SPINE bundle array length is three: selective predicate on raw `region` and `event_type`, group accumulator, sort on grouped metrics. Extra project stages or a trailing document-level region predicate after group break `pipeline_hash` and stage-digest grading.
