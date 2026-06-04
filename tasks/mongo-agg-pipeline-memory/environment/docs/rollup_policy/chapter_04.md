# Chapter 04 — Tail attachment

The tail attachment module concatenates optional trailing stages after the core bundle array is built.

For WK-SPINE:

- Tail stages must not re-introduce document-level `region` / `event_type` predicates after `$group` reshapes documents into `_id` + metric fields.
- Configuration keys on the bundle config object use `eventType` (camelCase) from workload profiles; document paths remain snake_case.
- A tail `$match` that references `cfg.event_type` (undefined on the profile object) drops every grouped row.

When tail attachment is disabled, the module returns the incoming stage array unchanged.
