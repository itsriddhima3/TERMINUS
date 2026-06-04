### Decision
GO — Attempt 1. Validated smart-meter NDJSON pipeline; oracle 1.0 and NOP 0.0 on harbor after parse/correction client fixes.

### Metadata
- Task name: java-meter-ndjson-reconcile
- Title: Java Meter NDJSON Reconciler
- Category: data-processing
- Languages: ["java", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["api_integration"]
- Tags: ["java", "spring-boot", "ndjson", "meter", "cli", "api"]
- Milestones: 3

### Discovery budget
- Discovery: Paginated NDJSON requires following X-Next-Cursor across two fixture pages
  Planned location: Spring Boot ReadingsController + /app/docs/api_contract.md
  Why instruction must not reveal it: Would collapse fetch to a single HTTP GET recipe

- Discovery: Correction keys must match API reading_at strings including Z suffix
  Planned location: CorrectionsClient + corrections.json fixture
  Why instruction must not reveal it: Agent must align timestamp normalization with API index keys

- Discovery: Tariff windows use exclusive end boundaries per bench precedence
  Planned location: /app/docs/tariff_window_notes.md vs archive docs
  Why instruction must not reveal it: Listing inclusive/exclusive rule makes normalize a transcription task

### Collapse audit
Stage: post-oracle

Smallest plausible successful patch: pagination loop + timestamp preserve + device join key + correction parse quote fix + three recon detectors.

Likely editable frontier: meter/ingest/NdjsonFetch.java, meter/ingest/CsvLookup.java, meter/net/CorrectionsClient.java, meter/recon/{GapDetect,DupDetect,DeltaCheck}.java

Collapse verdict: PASS — fixes distributed across fetch, normalize, and reconcile with doc precedence navigation.

### Oracle notes
Nine unified-diff patches across three milestones; solve scripts rebuild CLI and invoke meterctl verbs. Harbor evidence: oracle reward 1.0 (jobs/2026-06-03__00-06-45), NOP reward 0.0 (jobs/2026-06-02__23-59-43).
