<?php
declare(strict_types=1);

namespace OverlayInspect\Game;

use PDO;
use OverlayInspect\Persistence\Tally;
use OverlayInspect\Persistence\Audit;

final class Lifecycle {
    public function __construct(
        private readonly PDO $pdo,
        private readonly Tally $tally,
        private readonly Audit $audit,
    ) {}

    public function freshFor(string $challengeId): array {
        $now = getenv('SCRIPTED_CLOCK') === '1'
            ? 0
            : (int)floor(microtime(true) * 1000);
        $stmt = $this->pdo->prepare(
            'INSERT INTO sessions (challenge_id, opened_at_ms) VALUES (?, ?)'
        );
        $stmt->execute([$challengeId, $now]);
        $rowId = (int)$this->pdo->lastInsertId();
        $this->audit->record('open_session', json_encode([
            'session_row_id' => $rowId,
            'challenge_id' => $challengeId,
        ], JSON_THROW_ON_ERROR));
        return [
            'session_row_id' => $rowId,
            'challenge_id' => $challengeId,
            'opened_at_ms' => $now,
            'closed_at_ms' => 0,
            'hint_count' => 0,
            'mark_count' => 0,
            'bucket_start_ms' => 0,
            'bucket_count' => 0,
            'last_hint_at_ms' => 0,
            'fresh' => true,
        ];
    }

    public function restoreFor(int $sessionRowId): array {
        $stmt = $this->pdo->prepare('SELECT * FROM sessions WHERE session_row_id = ?');
        $stmt->execute([$sessionRowId]);
        $session = $stmt->fetch();
        if ($session === false) {
            throw new \RuntimeException("session not found: {$sessionRowId}");
        }
        $hintCount = $this->tally->countFor($sessionRowId, 'hint');
        $markCount = $this->tally->countFor($sessionRowId, 'mark');

        $lastHintStmt = $this->pdo->prepare(
            'SELECT * FROM hints WHERE session_row_id = ? ORDER BY hint_row_id DESC LIMIT 1'
        );
        $lastHintStmt->execute([$sessionRowId]);
        $lastHint = $lastHintStmt->fetch();

        $bucketStart = 0;
        $bucketCount = 0;
        $lastHintAt = 0;
        if ($lastHint !== false) {
            $bucketStart = (int)$lastHint['bucket_start_ms'];
            $lastHintAt = (int)$lastHint['raised_at_ms'];
            $countStmt = $this->pdo->prepare(
                'SELECT COUNT(*) AS c FROM hints WHERE session_row_id = ? AND bucket_start_ms = ?'
            );
            $countStmt->execute([$sessionRowId, $bucketStart]);
            $bucketCount = (int)$countStmt->fetch()['c'];
        }

        $this->audit->record('resume_session', json_encode([
            'session_row_id' => $sessionRowId,
        ], JSON_THROW_ON_ERROR));

        $this->pdo->prepare(
            'UPDATE sessions SET closed_reason = NULL WHERE session_row_id = ?'
        )->execute([$sessionRowId]);

        return [
            'session_row_id' => $sessionRowId,
            'challenge_id' => (string)$session['challenge_id'],
            'opened_at_ms' => (int)$session['opened_at_ms'],
            'closed_at_ms' => (int)($session['closed_at_ms'] ?? 0),
            'hint_count' => $hintCount,
            'mark_count' => $markCount,
            'bucket_start_ms' => $bucketStart,
            'bucket_count' => $bucketCount,
            'last_hint_at_ms' => $lastHintAt,
            'fresh' => false,
        ];
    }
}
