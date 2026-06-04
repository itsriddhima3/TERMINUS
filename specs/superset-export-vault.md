### Decision
GO — Attempt 1. Redesigned from greenfield AES-GCM CLI spec into a broken Superset export vault pipeline with three coordinated fix loci (field walk, envelope AAD, manifest digest) plus incomplete verify path.

### Metadata
- version: 2
- Task name: superset-export-vault
- Title: Export Vault Pipeline
- Category: security
- Languages: ["go", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific"]
- Tags: ["go", "cryptography", "superset", "export", "manifest"]
- Milestones: 0

## Authoring Brief

### Public contract
Agent repairs `/app` Go vault pipeline for Apache Superset export bundles. `/app/scripts/vault_audit.sh` writes `/app/output/vault_report.json` exercising fixtures from `/app/data/fixture_catalog.json` per `/app/data/scenario_matrix.json` with `/app/keys/test_master.key`. Rows `acme_seal_clean` and `nested_seal_clean` require `plaintext_hits` 0 and `manifest_ok` true. `tamper_reject` requires `verify_ok` false after ciphertext swap tamper. `roundtrip_acme` and `roundtrip_oauth` require `sha256_match` true with matching digests.

### Failure topology
Nested metadata secrets survive sealing; swapped ciphertext verifies on the broken path; restored archives diverge from fixture bytes. Operations notes misdirect toward scrypt escrow. Decoy walkers and digest helpers perform real non-fix work.

### Environment shape
Go module with `cmd/vaultctl`, internal walk/cipher/manifest/vault packages, bash audit harness, Superset-like export fixtures, redaction config, docs.

### Required artifacts
Standard single-step layout with 20+ environment files, tests, solve.sh installing fixed walk/cipher/manifest/service modules.

### Test plan
Eleven pytest cases covering schema, scenario rows, seal cleanliness, manifest verify, tamper rejection, round-trip digests, binary presence.

### Drafting guardrails
Symptoms-only instruction; opaque fix symbols `walk_q3`, `bind_m7`, `fold_r2`; no AES-GCM or AAD vocabulary in instruction.

### Triviality Ledger
- Top-level-only field walk passes acme flat seal but leaves nested OAuth/provider secrets plaintext.
- Metadata hash skip in verify accepts swapped ciphertext tamper while non-metadata checks still run.
- Line-trim manifest digest breaks byte-identical roundtrip even when decrypt restores values.
- Mutex-style red herring scrypt helper does not repair verify or roundtrip paths.

### Per-gate Pitfall Inventory
- RC1 — Oracle edits walk, cipher AAD, raw digest, and full verify loop.
- RC6 — Instruction omits algorithm names and fix-path identifiers.
- RC7 — solve.sh installs four substantive fixed modules.
- CR2 — flipping_point_contract splits walk, cipher, digest subsets.
- GX9 — Matrix expected bands documented in instruction prose.

### Initial Draft Commitments
- `tasks/superset-export-vault/instruction.md`
- `tasks/superset-export-vault/task.toml`
- `tasks/superset-export-vault/output_contract.toml`
- `tasks/superset-export-vault/environment/**` (34+ files)
- `tasks/superset-export-vault/solution/solve.sh`
- `tasks/superset-export-vault/solution/fixed/*.go`
- `tasks/superset-export-vault/tests/test.sh`
- `tasks/superset-export-vault/tests/test_outputs.py`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/internal/walk/paths.go
  symbol: walk_q3
  kind: function
  signature: func walk_q3(member string, payload []byte, rules config.RedactionDoc) ([]types.FieldHit, error)
  purpose: discovers redaction field paths in metadata members

- path: environment/internal/cipher/envelope.go
  symbol: bind_m7
  kind: function
  signature: func bind_m7(key []byte, a, b string, plain []byte) (string, error)
  purpose: seals plaintext field values into ENC tokens

- path: environment/internal/manifest/digest.go
  symbol: fold_r2
  kind: function
  signature: func fold_r2(member string, payload []byte) string
  purpose: computes per-member manifest digest
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/internal/walk/paths.go
    controls_tests: [test_acme_seal_no_plaintext, test_nested_seal_no_plaintext, test_nested_seal_manifest_ok, test_catalog_needles_absent_in_nested_sealed]
  - id: B
    path: environment/internal/cipher/envelope.go
    controls_tests: [test_tamper_reject]
  - id: C
    path: environment/internal/manifest/digest.go
    controls_tests: [test_roundtrip_acme_digest_match, test_roundtrip_oauth_digest_match, test_acme_seal_manifest_ok]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/internal/walk/legacy.go
  kind: helper
  rhymes_with: walk_q3
  non_fix_purpose: counts legacy sqlite dump password tokens

- path: environment/internal/cipher/scrypt_wrap.go
  kind: helper
  rhymes_with: bind_m7
  non_fix_purpose: scrypt-based escrow wrapping for offline secrets

- path: environment/internal/manifest/summary.go
  kind: helper
  rhymes_with: fold_r2
  non_fix_purpose: summarizes manifest counts for logging
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [superset, export, archive, bundles, credentials, oauth, client, secrets, yaml, json, metadata, encrypt, key, manifest, hashes, verify, decrypt, tamper, plaintext, roundtrip, audit, fixture, sealed, restored, digest, pipeline, vault, superset, apache]
```
