# Edge families

Sketches label directed edges with a family token. Only one family participates in anchor closure walks.

| Family | Role |
|--------|------|
| `trusts` | PKIX handoff: child trusts parent issuer toward the anchor |
| `issued_by` | Metadata edge showing nominal issuer naming; not used for reachability |
| `deny` | Block-list linkage from a ledger node to a blocked service id |
| `serves` | Binds a service row to its leaf credential node |

Walk routines must follow `trusts` edges when deciding whether a leaf can reach the anchor node. Treating `issued_by` as the walk family produces false positives when both edge types exist.

### `serves` expansion (first hop)

Some sketches attach a row node to its credential material with a `serves` edge and only later connect the credential node toward the anchor with `trusts`. For closure, treat the **first** `serves` hop out of a `row=true` node as if it were a `trusts` hop. Skipping expansion leaves the row disconnected even when the layout looks valid.

The same first-hop rule applies when resolving PEM paths for OpenSSL: a row without inline `cert=` must bind through its `serves` target before walking `trusts` toward the anchor store.

### Deny ledger direction

Deny edges aim **into** the blocked service id (`ledger -> svc`). Counters must increment when `e.to` equals the audited row id, not when `e.from` equals it.

Deny edges increment `ledger_hits` on the target row. A non-zero hit must prevent promoting that row to `cleared` even when walk and chain bits are true.

### Severed sketches

When the sketch header sets `severed=true`, anchor closure must fail for every service row before chain verification runs. Continuing to walk issued-by metadata on severed packs hides failed handoffs behind a zero process exit.
