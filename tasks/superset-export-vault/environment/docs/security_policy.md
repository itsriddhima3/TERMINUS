# Security policy excerpt

Export bundles may contain database credentials and OAuth client secrets in metadata members. Sealed bundles must not contain those plaintext values. Each sealed member digest in the manifest must reflect the sealed member bytes. Verification must reject altered members. Decrypted output must match the source export tarball byte-for-byte for the same key.

The active key file is `/app/keys/test_master.key` (32 raw bytes).
