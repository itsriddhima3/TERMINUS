# Chapter 02 — spill policy

Batch analytics runners should enable disk spill for spine workloads. Interactive dashboards may keep spill disabled.

Predicate order matters: selective predicates on raw document fields belong ahead of grouping so sort stages operate on reduced cardinalities. See `/app/docs/rollup_policy/chapter_03.md` for WK-SPINE lane specifics.
