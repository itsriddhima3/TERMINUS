# Chapter 01 — RAM budgets

Blocking stages such as grouping and sorting accumulate working sets in RAM until spill is permitted. Default per-process caps apply unless the invocation enables disk spill.

Wide grouping before selective predicates materialize the entire store into the working set and routinely trip the cap on large stores.
