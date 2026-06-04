# HS folding

Strip non-digits from `hs_raw`, then right-pad with zeros to length **10** for `hs10`. Example: `8471.30.00` becomes `8471300000`.

Older exporter notes mention a six-digit window; the live bench expects ten digits for API lookups. Chapter-99 style codes that already present ten digits after stripping punctuation should be kept at full width (do not truncate to six).
