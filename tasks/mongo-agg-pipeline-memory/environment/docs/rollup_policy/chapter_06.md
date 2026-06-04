# Chapter 06 — Audit contract alignment

`/app/app/pipeline_audit.sh` materializes the workload matrix report contract.

Graded fields include `allow_disk_enabled`, which reflects effective spill policy (invoke JSON plus wrapper), and `first_stage_kind` / `match_stage_index`, which reflect the live bundle array after tail attachment.

`examined_to_returned_ratio` compares selective scan volume to grouped row count when the first stage is a raw-field predicate.

`pipeline_hash` is a sixty-four character hex fingerprint of the serialized stage array; consecutive audit runs must agree. For WK-SPINE-EMEA, `grouped_keys` is one bucket and `result_total` must match a standalone events-store rollup that applies the same registry filters with batch spill enabled.
