# Meridian precedence memo

When volume 04 appendix errata disagrees with this memo, **this memo wins** for caller-facing behavior.

## Submission key reuse

Outbound submission tokens remain valid for **24 hours** measured from the acceptance anchor timestamp supplied at first probe or post. Retries inside that window MUST reuse the same token. After expiry, callers MAY mint a fresh token; already-settled intents MUST NOT be posted again.

## Beneficiary fingerprint

Beneficiary labels are normalized by trimming edges and collapsing internal whitespace runs before hashing. Labels that differ only by spacing (for example `Gamma  Vault` versus `GammaVault`) MUST map to the same fingerprint.

## Minor units

Amount fields in major-unit alias form (labels containing `major_alias`) with values below 10000 MUST be scaled to minor units (multiply by 100) before fingerprinting. Distinct cent amounts MUST NOT collapse.
