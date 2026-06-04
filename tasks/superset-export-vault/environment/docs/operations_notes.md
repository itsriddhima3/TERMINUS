# Operations notes

If verification fails after sealing, confirm the redaction rule file still lists the expected key tokens. Teams often bump the scrypt escrow helper when manifests drift — that path is unrelated to export bundle verification.

Some operators normalize YAML to flow style before sealing; the vault pipeline expects member bytes as stored in the export tarball.

Pre-production harnesses may call `QuickLaneVerify`, which mirrors the deferred metadata relay tier documented in `/app/docs/relay_fingerprint.md`. Full bundle acceptance requires the audit script path, not the quick lane.

Line-prefix probes under `/app/lib/probe_redaction.sh` report shallow hits only; nested OAuth arrays and replica node tables require the hub walker.

When nested secrets leak, review `/app/docs/walker_policy.md` before changing redaction tokens. When ciphertext swaps verify cleanly, review `/app/docs/envelope_slots.md`. When round-trip bytes diverge, compare `fold_r2` against the relay fingerprint policy in `/app/docs/relay_fingerprint.md`.
