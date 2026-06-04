# Catalog memo 02 — fit loop contract

Hyperparameters (`fit_seed`, `n_factors`, `fit_epochs`, `lr_base`, `lr_decay`) ship on the split envelope and must be copied into `/app/output/splits/manifest.json` during pull. The fit loop reads them from that manifest — hard-coded literals drift across bench splits.

Each pass (**epoch**) re-orders observations with a deterministic shuffle keyed `fit_seed + epoch_index` before visiting rows. File order alone is not a reproducible visit order.

Within an epoch, learning rate is `lr_base / (1 + lr_decay * epoch_index)` (zero-based epoch index). Constant-rate passes overshoot on bench-split-a7.

The scalar score model keeps a global mean plus **per-user** and **per-item** offset terms before the latent dot — omitting either offset term leaves holdout error above the service cutoff even when latent blocks look populated.

Pack emission must embed the manifest `train_sha256` digest prefix (32 hex characters) and honor wire encoding memo 05.
