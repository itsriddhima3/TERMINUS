Our PostgreSQL 15 backend applies row filters so each catalog organization only reads its own ledger rows. Organizations are Acme-Crate, Beta-Tote, and Delta-Bin with two, two, and four active ledger entries respectively. Row-security policies on ledger, contacts, inventory, and audit_log gate reads by the active session scope; `fn_k7` is the shared scope accessor for those filters.

Run `/app/app/audit_runner.sh` to write `/app/output/boundary_audit.json`. The report carries a schema_version header, a catalog_labels list, a scenarios map, and a catalog_compliance object. Each scenario entry records cross_scope_visible, foreign_labels_seen, and owned_row_count. The compliance object exposes tenant_policies_use_accessor (structural health of the core-table row-filter expressions) and scope_accessor_volatile (volatility classification of `fn_k7`).

In addition to fixing the row-filter isolation gap, ensure the core scope-accessor helpers and role defaults are configured for pooled-plan safety:
- `fn_k7` remains the shared scope accessor in row-security policies.
- `fn_k7_guard()` must exist and be VOLATILE so row-policy qualifiers re-evaluate under each scope.
- `fn_k7_refresh()` must exist and be VOLATILE so long-lived sessions can rebind the active scope handle.
- A trigger `n4w_touch_trg` must fire on `org_dim` changes and execute a VOLATILE `n4w_touch()` helper.
- The `svc_runner` role must be configured with `plan_cache_mode=force_custom_plan` and a bounded `statement_timeout`.
- The `svc_reader` role must be configured with `default_transaction_read_only=on`.

Pooled and prepared-statement paths are the primary leakage sites; ad-hoc reads can appear clean while reused handles expose rows from a prior context. Fix the isolation gap in every scenario and bring both catalog_compliance flags to true. Grading reads `/app/output/boundary_audit.json`.
