<?php
declare(strict_types=1);

namespace OverlayInspect\Game;

use PDO;
use OverlayInspect\Persistence\Tally;
use OverlayInspect\Persistence\Audit;

/**
 * Offline action-replay helper used by the administrative `describe`
 * command to project an old session back to the operator as a
 * human-readable transcript.
 *
 * Replay reads the persisted action rows for a (possibly closed)
 * session and prints them in sequence. It uses Tally only to
 * record an administrative "replayed" marker against the audit log
 * — it never writes to the action tables it is replaying from.
 * Replay is not invoked from the play loop.
 */
final class Replay {
    public function __construct(
        private readonly PDO $pdo,
        private readonly Tally $tally,
        private readonly Audit $audit,
    ) {}

    public function transcriptFor(int $sessionRowId): array {
        $hintsStmt = $this->pdo->prepare(
            'SELECT raised_at_ms, sequence_no, incurred_penalty, bucket_start_ms '
            . 'FROM hints WHERE session_row_id = ? ORDER BY sequence_no'
        );
        $hintsStmt->execute([$sessionRowId]);
        $hints = $hintsStmt->fetchAll();

        $marksStmt = $this->pdo->prepare(
            'SELECT raised_at_ms, sequence_no, input_col, input_row, matched, matched_region_id '
            . 'FROM marks WHERE session_row_id = ? ORDER BY sequence_no'
        );
        $marksStmt->execute([$sessionRowId]);
        $marks = $marksStmt->fetchAll();

        $events = [];
        foreach ($hints as $h) {
            $events[] = [
                'kind' => 'hint',
                'at_ms' => (int)$h['raised_at_ms'],
                'seq' => (int)$h['sequence_no'],
                'extra' => [
                    'incurred_penalty' => (int)$h['incurred_penalty'],
                    'bucket_start_ms' => (int)$h['bucket_start_ms'],
                ],
            ];
        }
        foreach ($marks as $m) {
            $events[] = [
                'kind' => 'mark',
                'at_ms' => (int)$m['raised_at_ms'],
                'seq' => (int)$m['sequence_no'],
                'extra' => [
                    'input_col' => (int)$m['input_col'],
                    'input_row' => (int)$m['input_row'],
                    'matched' => (int)$m['matched'],
                    'matched_region_id' => $m['matched_region_id'],
                ],
            ];
        }
        usort($events, static fn(array $a, array $b) => $a['at_ms'] <=> $b['at_ms']);

        $this->audit->record('replay_session', json_encode([
            'session_row_id' => $sessionRowId,
            'event_count' => count($events),
        ], JSON_THROW_ON_ERROR));
        return $events;
    }

    public function compact(int $sessionRowId): int {
        $stmt = $this->pdo->prepare(
            'SELECT COUNT(*) AS c FROM hints WHERE session_row_id = ?'
        );
        $stmt->execute([$sessionRowId]);
        return (int)$stmt->fetch()['c'];
    }
}
