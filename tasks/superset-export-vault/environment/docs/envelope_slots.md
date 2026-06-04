# Envelope slot binding

Each redacted metadata field is sealed into an `ENC:v1:` token. The sealing primitive accepts a **slot vector** assembled from the tarball member path and the dotted field path inside that member. Slot bytes are concatenated with a single NUL separator before they are handed to the AEAD primitive as associated data.

Manifest envelope identifiers use `member:field` keys. During verify, the ledger reopens each token with the same member and field path tuple used at seal time. Relocation of ciphertext across members breaks slot agreement even when the manifest row still parses.

The offline escrow helper under `pkg/k2n` uses a fixed slot label and does not participate in export bundle sealing.
