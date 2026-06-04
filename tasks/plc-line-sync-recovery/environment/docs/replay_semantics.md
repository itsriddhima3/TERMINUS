# PLC line replay semantics

How `/app/bin/line_audit` derives `sync_report.json` from the active assembly snapshot and station PLC segment logs. This is the line coordination protocol the Rust/Go pipeline should implement.

## Bundle inputs

The assembly snapshot supplies quorum size, split generation, jitter tight band, and trust anchor for stamp checks. Each station contributes replication lag and commit watermark metadata plus JSONL segment rows. Legacy field aliases (cluster pack, clock offset, cache watermark, split epoch) are accepted where the loader already maps them.

## Watermark and jitter

The replay watermark is the minimum commit watermark across stations. Jitter band is wide when the spread between the largest and smallest station replication lag exceeds the configured tight band; otherwise tight.

## Per-sequence reconciliation

Only rows with sequence strictly above the watermark participate in choosing a winning phase/payload group. All rows still feed stable phase once the cycle chain is known.

For each such sequence, partition rows by epoch and payload. A partition qualifies when at least quorum-size distinct stations contributed and at least quorum-size rows pass the wire integrity tag (sixteen-bit value from payload bytes XOR sequence, matching the row CRC field) through the trust-anchor stamp gate. Among qualifying partitions, select the one whose members have the smallest minimum of wall time minus that station’s replication lag.

Defect purges accumulate CRC-invalid rows inside the chosen partition. Skew drift max is the widest ttl_left spread among CRC-valid rows in that partition, using each row’s ttl_left or the deterministic fallback when zero. Orphan cycles counts sequences above the watermark with no qualifying partition. Stations live counts distinct members in CRC-valid rows of accepted partitions.

Line synced is false when the accepted epoch exceeds split generation but fewer than quorum CRC-valid members remain in that partition.

## Chain and phase

Cycle chain is the longest prefix starting at sequence one where each slot is either at or below the watermark or was accepted during reconciliation. Stable phase is the highest epoch among rows at or below the cycle chain that are CRC-valid on an accepted sequence, plus CRC-valid rows at or below the watermark even when that sequence was not re-accepted above it.

## Digest

Digest hex is SHA-256 over line id, stable phase, cycle chain, defect purges, orphan cycles, stations live, jitter band, line synced (encoded as the strings true or false), and skew drift max, pipe-separated in that order.
