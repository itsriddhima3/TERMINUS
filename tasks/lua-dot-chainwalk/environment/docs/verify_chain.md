# OpenSSL chain verification

When an intermediate store blob exists, `reconcile_b` must call:

```bash
openssl verify -CAfile <anchor_pem> -untrusted <intermediate_pem> <leaf_pem>
```

The anchor belongs in `-CAfile`. The issuing intermediate belongs in `-untrusted`. The leaf is the final positional argument.

Swapping anchor and intermediate in those flags often still prints `OK` on some OpenSSL builds while reporting an inverted trust path; the bundle must treat that as `chain_ok = false` when the wiring is reversed.

Single-hop chains (leaf signed directly by anchor) use:

```bash
openssl verify -CAfile <anchor_pem> <leaf_pem>
```
