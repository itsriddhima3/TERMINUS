<?php
declare(strict_types=1);

namespace OverlayInspect\Persistence;

use PDO;

/**
 * Append-only per-session event log writer.
 *
 * Records discrete actions (marks, hints) against a session row with a
 * caller-supplied sequence number. The writer is intentionally dumb: it
 * trusts the caller's seq value verbatim so that in-memory engine state
 * remains the single source of truth for ordering. Callers that don't
 * track seq locally can fall back to snapshot() + 1.
 */
final class Tally {
    public function __construct(private readonly PDO $pdo) {}

    public function note(int $sessionRowId, string $kind, array $payload): int {
        $seq = (int)($payload['seq'] ?? ($this->snapshot($sessionRowId, $kind) + 1));
        $raisedAt = (int)($payload['raised_at_ms'] ?? 0);
        if ($kind === 'mark') {
            $stmt = $this->pdo->prepare(
                'INSERT INTO marks (session_row_id, sequence_no, raised_at_ms, input_col, input_row, matched_region_id, matched)'
                . ' VALUES (?, ?, ?, ?, ?, ?, ?)'
            );
            $stmt->execute([
                $sessionRowId,
                $seq,
                $raisedAt,
                (int)($payload['input_col'] ?? 0),
                (int)($payload['input_row'] ?? 0),
                $payload['matched_region_id'] ?? null,
                (int)($payload['matched'] ?? 0),
            ]);
        } elseif ($kind === 'hint') {
            $stmt = $this->pdo->prepare(
                'INSERT INTO hints (session_row_id, sequence_no, raised_at_ms, incurred_penalty, bucket_start_ms)'
                . ' VALUES (?, ?, ?, ?, ?)'
            );
            $stmt->execute([
                $sessionRowId,
                $seq,
                $raisedAt,
                (int)($payload['incurred_penalty'] ?? 0),
                (int)($payload['bucket_start_ms'] ?? 0),
            ]);
        }
        return $seq;
    }

    public function snapshot(int $sessionRowId, string $kind): int {
        if ($kind === 'mark') {
            $stmt = $this->pdo->prepare(
                'SELECT COALESCE(MAX(sequence_no), 0) AS max_seq FROM marks WHERE session_row_id = ?'
            );
        } elseif ($kind === 'hint') {
            $stmt = $this->pdo->prepare(
                'SELECT COALESCE(MAX(sequence_no), 0) AS max_seq FROM hints WHERE session_row_id = ?'
            );
        } else {
            return 0;
        }
        $stmt->execute([$sessionRowId]);
        $row = $stmt->fetch();
        return (int)($row['max_seq'] ?? 0);
    }

    public function countFor(int $sessionRowId, string $kind): int {
        if ($kind === 'mark') {
            $stmt = $this->pdo->prepare('SELECT COUNT(*) AS c FROM marks WHERE session_row_id = ?');
        } elseif ($kind === 'hint') {
            $stmt = $this->pdo->prepare('SELECT COUNT(*) AS c FROM hints WHERE session_row_id = ?');
        } else {
            return 0;
        }
        $stmt->execute([$sessionRowId]);
        return (int)$stmt->fetch()['c'];
    }
}
