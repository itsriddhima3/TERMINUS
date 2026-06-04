Training should consume the manifest and jsonl from the prior fetch and write a reproducible pack to `/app/output/model/pack.bin`. Packs currently drift: header seed disagrees with manifest fit_seed, `train_sha256` prefix wrong length, global mean is off, visit order follows file order instead of epoch shuffles, learning rate never decays, offset terms stay zero, or int8 bands decode incorrectly after wire offset.

Pack layout and band-scale rules live in catalog memos 03 and 05. Fit loop contract is memo 02 — hyperparameters must come from manifest, not literals.

Run `ratectl train --manifest /app/output/splits/manifest.json --pack /app/output/model/pack.bin`. Signal completion when the pack matches the catalog contract.
